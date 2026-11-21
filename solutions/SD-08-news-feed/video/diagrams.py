#!/usr/bin/env python3
"""SD-08 news feed: every picture for the reference-solution video and the written design -> ./svg/*.svg.
One carried baseline (declared once), numbered flows, challenge overlays, C4, sequences, ERDs, figures.
The v3 mock-round figures are kept in .v3-mock-2026-11-20/ (their palette predates the colour-by-role rule).
Run: python3 diagrams.py"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import basesvg as bs
import c4svg as c4
import seqsvg as sq
import erdsvg as er

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
FONT = "Inter, Helvetica, Arial, sans-serif"
INK, RED, GREEN, BLUE, PURPLE, GREY, AMBER = "#24292f", "#c8341f", "#1f8a4c", "#2f6fb5", "#6b4fc4", "#8c959f", "#d18f1c"
def esc(s): return html.escape(str(s))

# ───────────────────────────── 1 · the carried baseline ──────────────────────────────────────────────
b = bs.Baseline(1600, 690, size=24)
A, B, C, D, E = 20, 360, 700, 1040, 1380          # columns: 150 px between joined boxes
TOP, MID, BOT, BH = 40, 250, 460, 110
# write lane (top)
b.node("author", A, TOP, 190, BH, "client", "Author", "posts")
b.node("postsvc", B, TOP, 190, BH, "service", "Post service", "post + outbox")
b.node("postsdb", C, TOP, 190, BH, "data", "Posts DB", "posts · author index", shape="db")
b.node("log", D, TOP, 200, BH, "queue", "Event log", "keyed by author", shape="queue", since=2)
b.node("fanout", E, TOP, 200, BH, "service", "Fan-out", "IDs · active only", since=2)
# middle row
b.node("graph", B, MID, 190, BH, "data", "Graph", "follows · blocks", shape="db")
b.node("celeb", D, MID, 200, BH, "cache", "Celebrity posts", "last 100 IDs", since=3)
b.node("timeline", E, MID, 200, BH, "cache", "Timelines", "500 IDs per user", since=2)
# read lane (bottom)
b.node("reader", A, BOT, 190, BH, "client", "Reader", "opens the app")
b.node("feed", B, BOT, 190, BH, "service", "Feed service", "merge · filter")
b.node("ranking", C, BOT, 190, BH, "ext", "Ranking", "another team")
b.node("postcache", D, BOT, 200, BH, "cache", "Post cache", "bodies by ID", since=2)
# tags: shown only in a challenge, a flow or the recap
b.node("synth", A, MID, 190, BH, "ext", "Synthetic users", "post and read", tag="ch8")
b.node("rebuild", E, BOT, 200, BH, "service", "Rebuild", "pull · coalesce", tag="ch5")

R = dict(src="r:0.3", dst="l:0.3")
b.edge("e1", "author", "postsvc", "POST", **R)
b.edge("e2", "postsvc", "postsdb", "one txn", **R)
b.edge("e3", "postsdb", "log", "outbox", **R)
b.edge("e4", "log", "fanout", "event", **R)
b.edge("e5", "fanout", "graph", "followers, paged", src="l:0.85", dst="t:0.5", via=[(1310, 133.5), (1310, 205), (455, 205)], at=(880, 193))
b.edge("e6", "fanout", "timeline", "insert IDs", src="b:0.6", dst="t:0.6", at=(1500, 200))
b.edge("e7", "fanout", "celeb", "one write", src="b:0.25", dst="t:0.5", via=[(1430, 232), (1140, 232)], since=3, kind="async", at=(1290, 222))
b.edge("e8", "reader", "feed", "GET /feed", **R)
b.edge("e9", "feed", "reader", "50 items", src="l:0.8", dst="r:0.8", kind="resp")
b.edge("e10", "feed", "graph", "follows, blocks", src="t:0.5", dst="b:0.5", at=(395, 400))
b.edge("e11", "feed", "postsdb", "200 author indexes", src="t:0.75", dst="l:0.75", via=[(502, 420), (640, 420), (640, 122.5)], until=1, at=(640, 280))
b.edge("e12", "feed", "celeb", "merge", src="t:0.75", dst="b:0.25", via=[(502, 412), (1090, 412)], since=3, at=(800, 400))
b.edge("e13", "feed", "timeline", "read IDs", src="t:0.92", dst="b:0.35", via=[(535, 440), (1450, 440)], since=2, at=(1290, 428))
b.edge("e14", "feed", "ranking", "rank", **R)
b.edge("e15", "ranking", "feed", "scores", src="l:0.75", dst="r:0.75", kind="resp")
b.edge("e16", "feed", "postcache", "hydrate", src="b:0.8", dst="b:0.5", via=[(512, 600), (1140, 600)], since=2, at=(820, 588))
b.edge("inv", "postsdb", "postcache", "invalidate", src="r:0.85", dst="l:0.33", via=[(965, 133.5), (965, 496.3)], tag="ch3", kind="async", at=(965, 300))
b.edge("e17", "feed", "rebuild", "miss: rebuild", src="b:0.3", dst="b:0.35", via=[(417, 630), (1450, 630)], tag="ch5", at=(1100, 618))
b.edge("e18", "rebuild", "timeline", "write back", src="t:0.6", dst="b:0.6", tag="ch5", at=(1500, 400))
b.edge("e19", "feed", "postsdb", "48 h", src="t:0.6", dst="l:0.8", via=[(474, 398), (632, 398), (632, 128)], tag="ch7", at=(632, 280))
b.edge("e20", "synth", "author", "post", src="t:0.5", dst="b:0.5", tag="ch8", kind="async")
b.edge("e21", "synth", "reader", "read", src="b:0.5", dst="t:0.5", tag="ch8", kind="async")

def sv(name, h, **view):
    b.h = h
    b.save(OUT / name, **view)
NOTE = lambda t, tone: []          # the slide carries the words; the picture stays large
H = 650
sv("base-v1.svg", 690, upto=1, legend=True)
sv("base-v2.svg", 690, upto=2, new=2, legend=True)
sv("base-v3.svg", 690, upto=3, new=3, legend=True)
ALL = ["ch3", "ch5", "ch7", "ch8"]
sv("base-final.svg", 690, upto=3, show=ALL, legend=True)
sv("map.svg", 690, upto=3, legend=True, attack=["fanout", "celeb", "timeline", "feed", "ranking"], keep=None)
sv("flow-fr1.svg", H, upto=3, flow=["e1", "e2", "e3", "e4", "e5", "e6"],
   notes=NOTE("An ordinary author: one transaction, one event, then post IDs into each active follower's timeline.", "blue"))
sv("flow-fr1c.svg", H, upto=3, flow=["e1", "e2", "e3", "e4", "e7"],
   notes=NOTE("A celebrity: the same event, and one write to the author's recent list. No fan-out.", "blue"))
sv("flow-fr2.svg", H, upto=3, flow=["e8", "e13", "e12", "e10", "e14", "e16", "e9"],
   notes=NOTE("Timeline, celebrity lists, blocks; rank inside a deadline; hydrate the top 50; return with a cursor.", "blue"))
sv("flow-fr3.svg", H, upto=3, flow=["e8", "e10", "e12"],
   notes=NOTE("Follow writes one edge. Nothing is backfilled: the next post, or the next read's merge, covers it.", "blue"))
sv("flow-fr4.svg", H, upto=3, show=["ch3"], flow=["e1", "e2", "inv", "e8", "e16"],
   notes=NOTE("Delete is one write to the post. The cache entry is dropped; hydration drops the ID on every page.", "blue"))
sv("ch1-attack.svg", H, upto=2, attack=["fanout"], keep=["log", "fanout", "timeline", "graph"], hot=["e4", "e5", "e6"],
   notes=NOTE("100 million followers: about 15 minutes of the whole fleet's fan-out, and everyone else waits behind it.", "red"))
sv("ch1-fix.svg", H, upto=3, fix=["celeb", "fanout"], keep=["log", "fanout", "celeb", "feed", "timeline"], ok=["e7", "e12"],
   notes=NOTE("Above the threshold: one write to the author's recent list. Readers merge the few celebrities they follow.", "green"))
sv("ch2-attack.svg", H, upto=3, attack=["fanout"], keep=["fanout", "celeb", "timeline"], hot=["e6", "e7"],
   notes=NOTE("A fixed number nobody can justify, and an account that crosses it overnight.", "red"))
sv("ch2-fix.svg", H, upto=3, fix=["fanout", "celeb", "timeline"], keep=["fanout", "celeb", "timeline", "feed"], ok=["e6", "e7", "e12", "e13"],
   notes=NOTE("The line from both sides of the arithmetic, as config. Crossing needs no backfill: the read merge covers it.", "green"))
sv("ch3-attack.svg", H, upto=3, attack=["timeline"], keep=["author", "postsvc", "postsdb", "timeline", "feed", "reader"], hot=["e13"],
   notes=NOTE("The deleted post's ID sits in three million timelines. Correctness stored in copies.", "red"))
sv("ch3-fix.svg", H, upto=3, show=["ch3"], fix=["feed", "postcache", "graph"], keep=["postsdb", "postcache", "feed", "graph", "reader"], ok=["inv", "e16", "e10"],
   notes=NOTE("Filter on read: hydrate from the post itself, drop blocked and unfollowed authors. Cleanup is cosmetic.", "green"))
sv("ch4-attack.svg", H, upto=3, attack=["timeline", "feed"], keep=["fanout", "timeline", "feed", "reader"], hot=["e6", "e9"],
   notes=NOTE("A re-delivered event inserts twice; an offset page repeats twelve posts and skips twelve.", "red"))
sv("ch4-fix.svg", H, upto=3, fix=["timeline", "feed"], keep=["fanout", "timeline", "feed", "reader"], ok=["e6", "e9"],
   notes=NOTE("A set keyed by post ID makes inserts idempotent; a cursor starts after the last item seen.", "green"))
sv("ch5-attack.svg", H, upto=3, attack=["timeline"], keep=["timeline", "feed", "postsdb", "reader"], hot=["e13"],
   notes=NOTE("A shard with 5 million users is gone. 1,700 rebuilds a second would mean 340,000 author-index reads a second.", "red"))
sv("ch5-fix.svg", H, upto=3, show=["ch5"], fix=["rebuild"], keep=["timeline", "feed", "rebuild", "reader"], ok=["e17", "e18"],
   notes=NOTE("Rebuild by pull, coalesced per user, rate-limited. Over the limit: a degraded feed now, a rebuild later.", "green"))
sv("ch6-attack.svg", H, upto=3, attack=["ranking"], keep=["feed", "ranking", "reader"], hot=["e14"],
   notes=NOTE("Ranking p99 goes from 70 ms to 300 ms; the feed waits for it and misses its 200 ms target.", "red"))
sv("ch6-fix.svg", H, upto=3, fix=["feed", "ranking"], keep=["feed", "ranking", "reader"], ok=["e14", "e15"],
   notes=NOTE("A hard deadline. On a miss: recency and close ties, or the session's last ranking. The fallback rate has an owner.", "green"))
sv("ch7-attack.svg", H, upto=3, attack=["timeline"], keep=["timeline", "feed", "reader"], hot=["e13"],
   notes=NOTE("A bounded, ranked view asked for 48 hours in time order. It does not hold the answer.", "red"))
sv("ch7-fix.svg", H, upto=3, show=["ch7"], fix=["postsdb"], keep=["postsdb", "feed", "reader"], ok=["e19"],
   notes=NOTE("Catch-up reads the source of truth, the followees' author indexes, through the rebuild path. Cached for minutes.", "green"))
sv("ch8-attack.svg", H, upto=3, attack=["fanout"], keep=["fanout", "celeb", "timeline", "feed"],
   notes=NOTE("Dashboards green. A routing bug made 30 % of mid-tier authors invisible to their followers.", "red"))
sv("ch8-fix.svg", H, upto=3, show=["ch8"], fix=["synth"], keep=["synth", "author", "reader", "feed", "fanout"], ok=["e20", "e21"],
   notes=NOTE("Synthetic authors in every tier post every minute; synthetic followers measure post-to-visible time.", "green"))
bs.budget_bar(OUT / "budget.svg", [("lookups + filter", 20, "cache"), ("ranking deadline", 80, "ext"), ("hydrate", 20, "cache"),
                                   ("network", 20, "edge")],
              total=200, unit="ms", title="One feed open, p99 (initial target 200 ms)")

# ───────────────────────────── 2 · C4 ────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 780)
d.node("au", 60, 80, 320, 160, "person", "Authors", "Person", "About 600 posts a second; a few have 100 M followers.")
d.node("rd", 60, 480, 320, 160, "person", "Readers", "Person", "500 M a day; about 90,000 feed opens a second at peak.")
d.node("fs", 640, 270, 360, 210, "system", "News feed system", "Software System", "Publishes posts, keeps bounded timelines, serves a ranked feed in 200 ms.")
d.node("rk", 1240, 60, 320, 150, "ext", "Ranking service", "External system", "Scores candidates; another team.")
d.node("gr", 1240, 300, 320, 150, "ext", "Social graph", "External system", "Who follows whom; blocks.")
d.node("md", 1240, 540, 320, 150, "ext", "Media CDN", "External system", "Images by URL; out of scope.")
d.edge("au", "fs", "Post", "HTTPS", src="r:0.6", dst="l:0.25", at=(500, 220))
d.edge("rd", "fs", "Open the feed", "HTTPS", src="r:0.4", dst="l:0.75", at=(500, 500))
d.edge("fs", "rk", "Score ~200 candidates", "80 ms budget", src="r:0.2", dst="l:0.6", at=(1120, 190))
d.edge("fs", "gr", "Followers, followees", "RPC, cached", src="r:0.5", dst="l:0.5", at=(1120, 360))
d.edge("rd", "md", "Fetch images", "HTTPS", src="b:0.5", dst="b:0.5", via=[(220, 740), (1400, 740)], at=(800, 728))
d.legend(40, 760, ("person", "system", "ext"))
d.save(OUT / "c4-context.svg")

d = c4.Diagram(1600, 950)
d.boundary(30, 50, 1180, 850, "News feed system", "Software System")
d.node("ps", 60, 100, 230, 150, "container", "Post service", "Service", "Writes post and outbox in one transaction.", size=20)
d.node("db", 360, 100, 230, 150, "db", "Posts DB", "Sharded store", "Posts by ID; author index by time.", size=20)
d.node("lg", 660, 100, 230, 150, "queue", "Event log", "Partitioned by author", "PostCreated, replayable.", size=20)
d.node("fo", 960, 100, 230, 150, "container", "Fan-out workers", "Consumers", "Route by tier; push IDs to active followers.", size=20)
d.node("tl", 960, 400, 230, 150, "db", "Timeline cache", "In memory", "500 post IDs per user.", size=20)
d.node("cc", 660, 400, 230, 150, "db", "Celebrity posts", "In memory, replicated", "Last 100 IDs per author.", size=20)
d.node("pc", 360, 400, 230, 150, "db", "Post cache", "In memory", "Hydrated posts by ID.", size=20)
d.node("fs", 60, 640, 530, 170, "container", "Feed service", "Stateless service", "Merge timeline and celebrities, filter, rank under a deadline, hydrate, cursor.", size=20)
d.node("rk", 1300, 640, 260, 150, "ext", "Ranking", "External", "Scores, 80 ms.")
d.node("gr", 1300, 300, 260, 150, "ext", "Social graph", "External", "Followers, blocks.")
d.edge("ps", "db", "post + outbox", "SQL", src="r", dst="l", at=(325, 85))
d.edge("db", "lg", "outbox relay", "CDC", src="r", dst="l", at=(625, 85))
d.edge("lg", "fo", "PostCreated", "consume", src="r", dst="l", at=(925, 85))
d.edge("fo", "tl", "insert IDs", "pipelined", src="b", dst="t", at=(1075, 320))
d.edge("fo", "cc", "one write", "", src="b:0.2", dst="t:0.6", at=(880, 330))
d.edge("fo", "gr", "followers", "paged", src="r:0.8", dst="t:0.5", via=[(1430, 220)], at=(1430, 270))
d.edge("fs", "tl", "timeline", "", src="r:0.2", dst="b:0.5", via=[(1075, 674)], at=(980, 600))
d.edge("fs", "cc", "celebrities", "", src="t:0.85", dst="b:0.5", via=[(510, 600), (775, 600)], at=(700, 588))
d.edge("fs", "pc", "hydrate 50", "multi-get", src="t:0.6", dst="b:0.5", at=(430, 600))
d.edge("fs", "rk", "rank", "deadline", src="r:0.6", dst="l:0.5", at=(950, 730))
d.legend(40, 930, ("container", "db", "queue", "ext"))
d.save(OUT / "c4-containers.svg")

# ───────────────────────────── 3 · sequences ─────────────────────────────────────────────────────────
def seq(name, parts, steps, **kw):
    s = sq.Seq(1800, size=23, row=50, **kw)
    for p in parts: s.part(*p)
    for st in steps:
        k = st[0]
        if k == "m": s.msg(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "r": s.ret(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "n": s.note(st[1], st[2], st[3], *(st[4:5]))
        elif k == "f": s.frame(st[1], st[2])
        elif k == "e": s.end()
    s.save(OUT / f"{name}.svg")

seq("seq-publish",
    [("au", "Author", "person"), ("ps", "Post service", "container"), ("db", "Posts DB", "db"), ("lg", "Event log", "queue"),
     ("fo", "Fan-out worker", "container"), ("tl", "Timelines", "db")],
    [("m", "au", "ps", "POST /posts, idempotency key"),
     ("m", "ps", "db", "one transaction: post row, author index, outbox row"),
     ("r", "ps", "au", "201, postId"),
     ("m", "db", "lg", "outbox relay: PostCreated, key = author", dict(kind="async")),
     ("m", "lg", "fo", "consume", dict(kind="async")),
     ("n", "fo", "fo", "tier = push; page through followers, skip inactive for 30 days"),
     ("m", "fo", "tl", "insert (postId, author, time); trim to 500", dict(hl=True)),
     ("n", "fo", "fo", "commit the log offset last: a crash re-delivers, never loses", "green")])

seq("seq-read",
    [("rd", "Reader", "person"), ("fs", "Feed service", "container"), ("tl", "Timeline", "db"), ("cc", "Celebrity posts", "db"),
     ("rk", "Ranking", "ext"), ("pc", "Post cache", "db")],
    [("m", "rd", "fs", "GET /feed?cursor"),
     ("m", "fs", "tl", "my timeline: about 500 IDs, ~5 ms"),
     ("m", "fs", "cc", "followed celebrities' recent IDs, ~5 ms"),
     ("n", "fs", "fs", "merge, de-duplicate, drop blocked and muted; top 200 by recency"),
     ("m", "fs", "rk", "score 200, deadline 80 ms", dict(hl=True)),
     ("m", "fs", "pc", "multi-get top 50, ~20 ms"),
     ("n", "fs", "fs", "drop anything deleted or out of audience", "green"),
     ("r", "fs", "rd", "50 items and a cursor")])

seq("seq-celebrity",
    [("st", "@star, 110 M", "person"), ("lg", "Event log", "queue"), ("fo", "Fan-out worker", "container"), ("cc", "Celebrity posts", "db"),
     ("rd", "Reader", "person"), ("fs", "Feed service", "container")],
    [("m", "st", "lg", "PostCreated, tier = pull", dict(kind="async")),
     ("m", "lg", "fo", "consume", dict(kind="async")),
     ("m", "fo", "cc", "append postId to @star's list: one write, not 110 million", dict(hl=True)),
     ("n", "fo", "fo", "the log partition is free again in milliseconds", "green"),
     ("m", "rd", "fs", "open the feed"),
     ("m", "fs", "cc", "lists for the 6 celebrities I follow"),
     ("n", "fs", "fs", "merge with my timeline; de-duplicate by postId", "green"),
     ("r", "fs", "rd", "one ranked feed")])

seq("seq-tier",
    [("gr", "Graph", "ext"), ("tj", "Tier job", "container"), ("fo", "Fan-out worker", "container"), ("tl", "Timelines", "db"), ("cc", "Celebrity posts", "db")],
    [("n", "gr", "gr", "@newstar: 9,000 followers on Monday, 2 M on Tuesday", "amber"),
     ("m", "gr", "tj", "follower counts, hourly", dict(kind="async")),
     ("n", "tj", "tj", "up at 100 k, down only below 50 k: no flapping"),
     ("m", "tj", "fo", "tier(@newstar) = pull", dict(hl=True)),
     ("m", "fo", "cc", "new posts: one write each"),
     ("n", "tl", "tl", "yesterday's pushed IDs stay and age out: no backfill, no removal", "green"),
     ("n", "cc", "cc", "readers' merge shows the new posts from the first minute", "green")])

seq("seq-delete",
    [("au", "Author", "person"), ("db", "Posts DB", "db"), ("pc", "Post cache", "db"), ("rd", "Reader", "person"),
     ("fs", "Feed service", "container"), ("cj", "Cleanup job", "container")],
    [("m", "au", "db", "DELETE post: one write, status = deleted", dict(hl=True)),
     ("m", "db", "pc", "invalidate postId", dict(kind="async")),
     ("m", "rd", "fs", "open the feed"),
     ("n", "fs", "fs", "drop authors I block, mute or unfollowed (a small set)"),
     ("m", "fs", "pc", "hydrate"),
     ("r", "pc", "fs", "miss, then the row says deleted: dropped"),
     ("n", "pc", "cj", "later, a cleanup job removes stale IDs from timelines: cosmetic", "green")])

seq("seq-dedupe",
    [("w3", "Worker W3", "container"), ("w7", "Worker W7", "container"), ("tl", "Timeline (a set)", "db"), ("rd", "Reader", "person"), ("fs", "Feed service", "container")],
    [("m", "w3", "tl", "insert p9 into 1,000 timelines"),
     ("n", "w3", "w3", "crash before committing the offset", "red"),
     ("m", "w7", "tl", "re-delivered: insert p9 again"),
     ("n", "tl", "tl", "the set is keyed by postId: no change", "green"),
     ("m", "rd", "fs", "GET /feed?cursor = (score 0.82, p51)"),
     ("r", "fs", "rd", "next 50 strictly after p51, from the session's ranked list", dict(hl=True))])

seq("seq-rebuild",
    [("rd", "Readers", "person"), ("fs", "Feed service", "container"), ("tl", "Timeline cache", "db"), ("ai", "Author indexes", "db"), ("rl", "Rebuild limiter", "container")],
    [("m", "rd", "fs", "open the feed"),
     ("m", "fs", "tl", "get timeline"),
     ("r", "tl", "fs", "empty: shard lost"),
     ("m", "fs", "rl", "rebuild token? (one in flight per user)", dict(hl=True)),
     ("f", "alt", "token granted"),
     ("m", "fs", "ai", "followees' recent posts, merged"),
     ("m", "fs", "tl", "write the rebuilt timeline back"),
     ("e",),
     ("f", "alt", "over the limit"),
     ("r", "fs", "rd", "degraded feed now: celebrities + top-20 followees' recent posts"),
     ("e",)])

seq("seq-rank",
    [("fs", "Feed service", "container"), ("rk", "Ranking", "ext"), ("pc", "Post cache", "db"), ("rd", "Reader", "person")],
    [("m", "fs", "rk", "score 200 candidates, deadline 80 ms"),
     ("n", "fs", "fs", "80 ms pass with no answer", "red"),
     ("n", "fs", "fs", "fallback: recency plus close ties, or the session's last ranking", "green"),
     ("m", "fs", "pc", "hydrate top 50"),
     ("r", "fs", "rd", "feed in 140 ms; response flagged fallback = true", dict(hl=True)),
     ("r", "rk", "fs", "late scores arrive: dropped, counted", dict(colour=GREY))])

seq("seq-catchup",
    [("rd", "Reader", "person"), ("fs", "Feed service", "container"), ("cu", "Catch-up cache", "db"), ("ai", "Author indexes", "db")],
    [("m", "rd", "fs", "GET /catchup?since=48h"),
     ("m", "fs", "cu", "cached result for this user?"),
     ("r", "cu", "fs", "miss"),
     ("m", "fs", "ai", "for each followee: posts since t-48h (the rebuild path)", dict(hl=True)),
     ("n", "fs", "fs", "merge by time; same visibility filter; page by (time, postId)", "green"),
     ("m", "fs", "cu", "store for 10 minutes"),
     ("r", "fs", "rd", "first 50, chronological, and a cursor")])

seq("seq-probe",
    [("sa", "Synthetic author", "container"), ("fo", "Fan-out", "container"), ("sf", "Synthetic follower", "container"), ("mt", "Metrics", "ext")],
    [("m", "sa", "fo", "post every minute, one author per tier"),
     ("m", "fo", "sf", "delivered by the real path", dict(kind="async")),
     ("m", "sf", "sf", "open the feed every 5 s until the post appears"),
     ("m", "sf", "mt", "post-to-visible time, per tier"),
     ("n", "mt", "mt", "mid tier: not visible after 5 min: page, with the tier", "red")])

# ───────────────────────────── 4 · data models ───────────────────────────────────────────────────────
c = er.Chen(1600, 940, size=26)
c.entity("u", 300, 380, "USER"); c.entity("p", 1150, 380, "POST"); c.entity("t", 1150, 740, "TIMELINE ENTRY", weak=True)
c.rel("au", 720, 380, "AUTHORS"); c.rel("fo", 300, 700, "FOLLOWS"); c.rel("bl", 300, 110, "BLOCKS"); c.rel("in", 720, 740, "SEES", identifying=True)
c.attr("uid", 100, 300, "user_id", of="u", key=True); c.attr("tier", 100, 470, "tier", of="u", derived=True)
c.attr("seen", 520, 250, "last_seen_day", of="u")
c.attr("pid", 1150, 220, "post_id", of="p", key=True); c.attr("aud", 1400, 300, "audience", of="p"); c.attr("st", 1400, 460, "status", of="p")
c.attr("sc", 1420, 740, "score", of="t", partial=True)
c.link("u", "au", "1"); c.link("au", "p", "N", total=True)
c.link("u", "fo", "M", src="b", dst="t", role="follower"); c.link("u", "bl", "M", src="t", dst="b")
c.link("u", "in", "1", src="b:0.8", dst="l"); c.link("in", "t", "N", total=True)
c.link("p", "t", "1", src="b", dst="t")
c.legend(1235, 20)
c.note(420, 850, 1000, "Timeline entries are derived: delete them all and the feed can be rebuilt from posts and follows.")
c.save(OUT / "erd-chen.svg")

e = er.ERD(1600, 820, size=22)
e.entity("post", 30, 40, 470, "post", [("post_id", "bigint", "PK"), ("author_id", "bigint", "IX"), ("text", "text", ""),
         ("media_refs", "text[]", ""), ("audience", "smallint", ""), ("status", "smallint", ""), ("created_at", "ts", "")],
         kind="focus", caption="source of truth; ID is time-sortable")
e.entity("ai", 570, 40, 450, "author_index", [("author_id", "bigint", "PK"), ("created_at", "ts", "PK desc"), ("post_id", "bigint", "")],
         caption="one partition per author: pull, rebuild, catch-up")
e.entity("fol", 1090, 40, 480, "follow (both directions)", [("user_id", "bigint", "PK"), ("followee_id", "bigint", "PK"), ("since", "ts", "")],
         kind="ext", caption="owned by the graph service")
e.entity("tl", 30, 450, 470, "timeline:{viewer}", [("post_id", "member", ""), ("author_id", "packed", ""), ("time", "score", "")],
         kind="redis", caption="sorted set, at most 500, by viewer")
e.entity("cc", 570, 450, 450, "celebrity_recent:{author}", [("post_id", "list", ""), ("(last 100)", "", "")],
         kind="redis", caption="replicated to many cache nodes")
e.entity("bl", 1090, 450, 480, "blocks:{viewer}", [("user_id", "set", ""), ("(blocks, mutes, unfollowed)", "", "")],
         kind="redis", caption="small; read on every open")
e.note(30, 760, 1540, "500 M users × 500 entries × 16 B = 4 TB of timelines. Bodies instead of IDs would be about 250 TB.")
e.save(OUT / "erd-physical.svg")

# ───────────────────────────── 5 · figures ───────────────────────────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{fill}">{esc(s)}</text>'
def R(x, y, w, h, fill, stroke, dash=False, rx=8, sw=2.2):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"{" stroke-dasharray=\"10 6\"" if dash else ""}/>')
def L(x1, y1, x2, y2, col=INK, sw=2.4, dash=False):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}"{" stroke-dasharray=\"8 6\"" if dash else ""}/>'

def tail():
    p = [T(40, 44, "Followers per account, log scale, illustrative: the tail decides the design", 28, INK, 800)]
    x0, W = 330, 1150
    import math
    sc = lambda v: x0 + W * math.log10(v) / 8.3
    rows = [("median account", 200, BLUE, "~200"), ("top 1 %", 1e4, BLUE, "~10,000"), ("top 0.01 %", 1e6, AMBER, "~1 million"), ("the largest", 1.1e8, RED, "110 million")]
    for i, (lab, v, col, txt) in enumerate(rows):
        y = 100 + i * 80
        fill = {BLUE: "#dbeafe", AMBER: "#fdf3e1", RED: "#fdecea"}[col]
        p += [T(40, y + 34, lab, 25, INK, 700), R(x0, y, sc(v) - x0, 50, fill, col), T(sc(v) + 14, y + 35, txt, 25, col, 800)]
    for v, lb in ((1e2, "100"), (1e4, "10 k"), (1e6, "1 M"), (1e8, "100 M")):
        p += [L(sc(v), 90, sc(v), 425, GREY, 1.5, True), T(sc(v), 452, lb, 20, "#57606a", 600, "middle")]
    p += [T(40, 505, "One post's push cost is its author's follower count. The few accounts on the right decide the architecture.", 25, "#5a1308", 700)]
    (OUT / "tail.svg").write_text(svgdoc(1600, 540, "".join(p)))
tail()

def tension():
    p = [T(40, 44, "Write amplification against read cost, per post, as followers grow (illustrative)", 28, INK, 800)]
    x0, x1, y0, y1 = 160, 1480, 420, 110
    p += [L(x0, y0, x1, y0, INK, 2.5), L(x0, y0, x0, y1 - 20, INK, 2.5),
          T(x0, y0 + 80, "followers of the author, log scale", 22, "#57606a", 600, "start"), T(x0 - 10, y1 - 30, "cost", 22, "#57606a", 600, "start")]
    import math
    X = lambda f: x0 + (x1 - x0) * math.log10(f) / 8
    pts = " ".join(f"{X(10 ** (i / 10)):.0f},{y0 - min(300, 300 * (10 ** (i / 10)) / 1e5):.0f}" for i in range(0, 81))
    p.append(f'<polyline points="{pts}" fill="none" stroke="{RED}" stroke-width="4"/>')
    p.append(L(x0, y0 - 60, x1, y0 - 60, BLUE, 4))
    p += [T(X(1e6) + 20, 140, "push: one insert per follower", 24, RED, 800), T(X(10) , y0 - 74, "pull: a small read on every follower's open", 24, BLUE, 800)]
    tx = X(1e4)
    p += [L(tx, y1, tx, y0, AMBER, 3, True), T(tx, y1 - 10, "threshold ≈ 10⁴–10⁵", 24, "#4a3207", 800, "middle")]
    p += [T(X(30), y0 + 40, "push wins", 24, GREEN, 800, "middle"), T(X(3e6), y0 + 40, "pull wins", 24, GREEN, 800, "middle")]
    p += [R(160, 520, 1320, 60, "#fdf3e1", AMBER), T(820, 558, "The hybrid follows the lower curve: push below the line, pull above it.", 25, "#4a3207", 800, "middle")]
    (OUT / "tension.svg").write_text(svgdoc(1600, 610, "".join(p)))
tension()

def memory():
    p = [T(40, 44, "Timeline tier memory: IDs against bodies (500 M users × 500 entries)", 28, INK, 800)]
    x0, W = 380, 1100
    sc = W / 250
    rows = [("IDs, 16 B each", 4, GREEN, "4 TB"), ("IDs, three replicas", 12, GREEN, "12 TB"), ("Bodies, ~1 KB each", 250, RED, "250 TB")]
    for i, (lab, tb, col, txt) in enumerate(rows):
        y = 100 + i * 90
        p += [T(40, y + 36, lab, 25, INK, 700), R(x0, y, max(tb * sc, 6), 54, "#e7f4ec" if col == GREEN else "#fdecea", col),
              T(x0 + max(tb * sc, 6) + 14, y + 37, txt, 25, col, 800)]
    p += [T(40, 410, "Bodies are 60 times larger, and every edit or delete would have to chase millions of copies.", 25, "#5a1308", 700),
          T(40, 455, "IDs are hydrated from one post cache: a delete is one write.", 25, "#173d24", 700)]
    (OUT / "memory.svg").write_text(svgdoc(1600, 500, "".join(p)))
memory()

def rebuildwave():
    p = [T(40, 44, "A lost shard: rebuilds a second, with and without a limit (illustrative)", 28, INK, 800)]
    x0, x1, y0, y1 = 160, 1480, 400, 100
    p += [L(x0, y0, x1, y0, INK, 2.5), L(x0, y0, x0, y1, INK, 2.5), T(x1, y0 + 40, "minutes after the loss", 22, "#57606a", 600, "end")]
    import math
    X = lambda m: x0 + (x1 - x0) * m / 60
    Y = lambda r: y0 - (y0 - y1) * r / 2000
    unl = " ".join(f"{X(m):.0f},{Y(1700 * math.exp(-m / 12)):.0f}" for m in range(0, 61))
    p.append(f'<polyline points="{unl}" fill="none" stroke="{RED}" stroke-width="4"/>')
    p.append(L(X(0), Y(500), X(35), Y(500), GREEN, 4))
    p += [T(X(2) + 10, Y(1700) + 6, "unlimited: 1,700/s × 200 reads = 340,000 author-index reads/s", 23, RED, 800),
          T(X(36) + 10, Y(500) + 8, "limited: 500/s (100,000 reads/s), the rest degraded", 23, GREEN, 800)]
    p += [L(X(0), Y(500), X(0), y0, GREY, 1), T(x0 - 14, Y(500) + 8, "500", 20, "#57606a", 600, "end"), T(x0 - 14, Y(1700) + 8, "1,700", 20, "#57606a", 600, "end")]
    p += [T(40, 470, "The limit decides the blast radius; the degraded feed keeps the lost users served while they wait.", 25, INK, 700)]
    (OUT / "rebuild-wave.svg").write_text(svgdoc(1600, 510, "".join(p)))
rebuildwave()

print(sorted(p.name for p in OUT.glob("*.svg") if p.stat().st_mtime > 0)[:3], len(list(OUT.glob("*.svg"))))
