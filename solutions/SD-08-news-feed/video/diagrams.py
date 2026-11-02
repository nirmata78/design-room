#!/usr/bin/env python3
"""C4, sequence and follow-up diagrams for the SD-08 news-feed video → ./svg/*.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg}.py.  Run: python3 diagrams.py
Content follows ../../SD-08-news-feed.md; the follow-up diagrams (fu-*) are new for this video."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq
from erdsvg import ERD

OUT = pathlib.Path(__file__).resolve().parent / "svg"
OUT.mkdir(exist_ok=True)
GREEN, GREEN_BG, RED, RED_BG, BLUE, BLUE_BG = "#2d8a4e", "#e7f4ec", "#c8341f", "#fdecea", "#2f6fb5", "#e8f0fa"

def seq(size=22, row=50):
    return sq.Seq(1500, size=size, row=row, head=66)

# ── C4 level 1: system context ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 780)
d.node("auth", 40, 60, 320, 150, "person", "Authors", "Person", "~600 posts a second; a few have 100 M followers")
d.node("read", 40, 520, 320, 150, "person", "Readers · 500 M DAU", "Person", "~75 k feed opens a second at peak")
d.node("feed", 620, 270, 380, 210, "focus", "News feed system", "Software System",
       "Publishes posts, keeps bounded timelines, serves a ranked feed in 200 ms")
d.node("rank", 1240, 60, 320, 150, "ext", "Ranking service", "External System", "scores candidates; owned by another team")
d.node("graph", 1240, 300, 320, 150, "ext", "Social graph", "External System", "followers and followees, cached")
d.node("media", 1240, 540, 320, 150, "ext", "Media CDN", "External System", "images served by URL; out of scope")
d.edge("auth", "feed", "Post", "HTTPS", src="r:0.5", dst="l:0.2", at=(490, 150), width=120)
d.edge("read", "feed", "Open feed", "HTTPS", src="r:0.5", dst="l:0.8", at=(490, 560), width=130)
d.edge("feed", "rank", "Score ~200 candidates", "80 ms budget", src="r:0.2", dst="l:0.5", at=(1120, 150), width=220)
d.edge("feed", "graph", "Who follows whom", "", src="r:0.5", dst="l:0.5", at=(1120, 345), width=190)
d.edge("read", "media", "Fetch images", "", src="b:0.5", dst="b:0.5", via=[(200, 740), (1400, 740)], at=(800, 740), width=150)
d.legend(40, 760, ("person", "focus", "ext"))
d.save(OUT / "c4-context.svg")

# ── C4 level 2: the write path ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.boundary(240, 20, 1340, 760, "News feed system")
d.node("cl", 20, 80, 190, 130, "person", "Author", "Person")
d.node("ps", 300, 70, 260, 150, "container", "Post service", "Container", "writes post + outbox in one transaction")
d.node("pdb", 300, 330, 260, 150, "db", "Posts DB", "sharded, time-sortable IDs", "source of truth + author index")
d.node("log", 660, 330, 280, 150, "queue", "Post-created log", "partitioned by author", "replayable; many consumers")
d.node("fo", 1040, 330, 260, 150, "focus", "Fan-out workers", "Container", "page followers, skip inactive")
d.node("tl", 1040, 600, 260, 140, "db", "Timeline cache", "Redis-class, by user", "~500 IDs per user")
d.node("cel", 660, 600, 280, 140, "db", "Celebrity recent posts", "hot cache", "last ~100 IDs per author")
d.node("g", 1380, 70, 180, 150, "ext", "Social graph", "External")
d.edge("cl", "ps", "POST", "", src="r:0.5", dst="l:0.5", at=(255, 125), width=60)
d.edge("ps", "pdb", "txn", "", src="b:0.5", dst="t:0.5", at=(430, 275), width=50)
d.edge("pdb", "log", "outbox / CDC", "", src="r:0.5", dst="l:0.5", at=(610, 385), width=100)
d.edge("log", "fo", "normal authors", "", src="r:0.5", dst="l:0.5", at=(990, 385), width=110)
d.edge("log", "cel", "celebrities", "", src="b:0.5", dst="t:0.5", at=(800, 545), width=100)
d.edge("fo", "tl", "insert IDs, trim to 500", "", src="b:0.5", dst="t:0.5", at=(1170, 545), width=190)
d.edge("fo", "g", "followers, paged", "", src="t:0.6", dst="b:0.5", via=[(1196, 280), (1470, 280)], at=(1330, 270), width=140)
d.note(20, 330, 200, "Store IDs, never bodies: 4 TB, not 250 TB.", size=17, colour=RED, bg=RED_BG)
d.save(OUT / "c4-containers-write.svg")

# ── C4 level 2: the read path ────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.boundary(240, 20, 1060, 690, "News feed system")
d.node("cl", 20, 300, 190, 140, "person", "Reader", "Person")
d.node("fs", 300, 290, 300, 160, "focus", "Feed service", "Container", "merge, dedup, filter, rank, hydrate")
d.node("tl", 700, 60, 280, 130, "db", "Timeline cache", "by user", "~500 IDs")
d.node("cel", 700, 260, 280, 130, "db", "Celebrity recent posts", "hot cache", "replicated widely")
d.node("pc", 700, 460, 280, 130, "db", "Post cache", "multi-get", "hydrated bodies")
d.node("pdb", 1020, 460, 240, 130, "db", "Posts DB", "source of truth")
d.node("rank", 1360, 160, 200, 140, "ext", "Ranking", "other team", "80 ms deadline")
d.node("g", 1360, 560, 200, 140, "ext", "Social graph", "External", "followed celebrities")
d.edge("cl", "fs", "GET /feed", "", src="r:0.5", dst="l:0.5", at=(255, 345), width=90)
d.edge("fs", "tl", "1 read", "", src="t:0.5", dst="l:0.5", via=[(450, 125)], at=(560, 110), width=70)
d.edge("fs", "cel", "5–20 reads", "", src="r:0.3", dst="l:0.5", at=(650, 300), width=100)
d.edge("fs", "pc", "top 50", "", src="b:0.5", dst="l:0.5", via=[(450, 525)], at=(560, 510), width=70)
d.edge("pc", "pdb", "miss", "", src="r:0.5", dst="l:0.5", at=(1000, 505), width=50)
d.edge("fs", "rank", "score 200", "", src="r:0.15", dst="l:0.5", via=[(1100, 314), (1100, 230)], at=(1180, 214), width=100)
d.edge("fs", "g", "followed celebrities", "", src="b:0.8", dst="b:0.5", via=[(540, 730), (1460, 730)], at=(1000, 730), width=190)
d.note(20, 560, 200, "Ranking slow? Fall back to recency inside the deadline.", size=17, colour=GREEN, bg=GREEN_BG)
d.save(OUT / "c4-containers-read.svg")

# ── C4 level 3: inside the feed service ──────────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
d.boundary(240, 20, 960, 720, "Feed service", "Container")
d.node("cl", 20, 80, 190, 130, "person", "Reader", "Person")
d.node("asm", 300, 70, 360, 140, "component", "Candidate assembler", "Component", "timeline + celebrity lists, ~200 IDs")
d.node("flt", 760, 70, 380, 140, "component", "Filter", "Component", "deleted posts, blocks, unfollows")
d.node("rk", 760, 300, 380, 140, "focus", "Ranking client", "Component", "deadline 80 ms; recency fallback")
d.node("hyd", 760, 530, 380, 140, "component", "Hydrator", "Component", "multi-get top 50; drop misses")
d.node("rb", 300, 300, 360, 140, "component", "Rebuilder", "Component", "pull from author indexes; coalesced")
d.node("cur", 300, 530, 360, 140, "component", "Cursor codec", "Component", "(score, postId): stable pages")
d.node("rank", 1340, 300, 230, 140, "ext", "Ranking service", "External")
d.node("pc", 1340, 530, 230, 140, "db", "Post cache", "")
d.edge("cl", "asm", "GET /feed", "", src="r:0.5", dst="l:0.5", at=(255, 125), width=90)
d.edge("asm", "flt", "", src="r:0.5", dst="l:0.5")
d.edge("flt", "rk", "", src="b:0.5", dst="t:0.5")
d.edge("rk", "hyd", "", src="b:0.5", dst="t:0.5")
d.edge("rk", "rank", "score", "", src="r:0.5", dst="l:0.5", at=(1240, 355), width=70)
d.edge("hyd", "pc", "", src="r:0.5", dst="l:0.5")
d.edge("asm", "rb", "timeline missing", "", src="b:0.5", dst="t:0.5", at=(480, 255), width=160)
d.edge("hyd", "cur", "", src="l:0.5", dst="r:0.5")
d.save(OUT / "c4-component-feed.svg")

# ── Sequence: publish by a normal author ─────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Author", "person"), ("ps", "Post service", "container"), ("db", "Posts DB + outbox", "db"),
                    ("log", "Post-created log", "queue"), ("fo", "Fan-out worker", "focus"), ("g", "Social graph", "ext"),
                    ("tl", "Timeline cache", "db")]:
    s.part(pid, lab, k)
s.msg("a", "ps", "POST /posts, idempotency key")
s.msg("ps", "db", "post + outbox row, one transaction", hl=True)
s.ret("ps", "a", "201 {postId}")
s.msg("db", "log", "CDC: PostCreated, key = author", "async")
s.msg("log", "fo", "consume")
s.frame("loop", "followers, a page at a time")
s.msg("fo", "g", "next page of followers")
s.msg("fo", "fo", "skip inactive for 30 days")
s.msg("fo", "tl", "insert (postId, author, ts), trim 500", hl=True)
s.end()
s.save(OUT / "seq-publish.svg")

# ── Sequence: reading the feed ───────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("r", "Reader", "person"), ("fs", "Feed service", "focus"), ("tl", "Timeline cache", "db"),
                    ("cel", "Celebrity cache", "db"), ("rk", "Ranking", "ext"), ("pc", "Post cache", "db")]:
    s.part(pid, lab, k)
s.msg("r", "fs", "GET /feed?cursor")
s.msg("fs", "tl", "my timeline: ~500 IDs · ~5 ms")
s.msg("fs", "cel", "followed celebrities' recent IDs · ~5 ms")
s.msg("fs", "fs", "merge, dedup, filter, top ~200 by recency", hl=True)
s.msg("fs", "rk", "score 200, deadline 80 ms")
s.frame("alt", "ranking late")
s.msg("fs", "fs", "use recency order")
s.end()
s.msg("fs", "pc", "multi-get top 50 · ~20 ms")
s.ret("fs", "r", "50 items + next cursor · ~110 ms p50", hl=True)
s.save(OUT / "seq-read.svg")

# ── The fan-out tiers: push, push-to-active, pull ────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
tiers = [("n", "Under ~10 k followers", "push", "fan out to every active follower", "container"),
         ("m", "~10 k to ~100 k", "push, narrower", "only followers active in the last day", "component"),
         ("c", "Over ~100 k", "pull", "recent posts cached per author, merged at read", "focus")]
for i, (nid, h, t, desc, k) in enumerate(tiers):
    d.node(nid, 40 + i * 520, 70, 480, 230, k, h, t, desc, size=27)
d.note(40, 360, 1520, "The threshold is a config value: where one post's fan-out cost exceeds the extra read cost "
       "across that author's followers. Start at ten thousand, then measure.", size=22, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "fanout-tiers.svg")

# ── Sequence: celebrity post and read-time merge ─────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("c", "Celebrity · 100 M", "person"), ("log", "Post-created log", "queue"),
                    ("cel", "Celebrity cache", "focus"), ("r", "Reader", "person"), ("fs", "Feed service", "container"),
                    ("tl", "Timeline cache", "db")]:
    s.part(pid, lab, k)
s.msg("c", "log", "post (via post service)")
s.msg("log", "cel", "append ID to the author's list: one write, not 100 M", hl=True)
s.note("log", "tl", "No fan-out. 100 M inserts would take ~100 s even at 1 M a second.", "red")
s.msg("r", "fs", "open feed")
s.msg("fs", "tl", "my timeline")
s.msg("fs", "cel", "lists for the celebrities I follow")
s.msg("fs", "fs", "merge both, dedup by postId", hl=True)
s.ret("fs", "r", "one ranked feed")
s.save(OUT / "seq-celebrity.svg")

# ── Sequence: delete or block, enforced on the read path ─────────────────────────────────────────
s = seq()
for pid, lab, k in [("a", "Author", "person"), ("pdb", "Posts DB", "db"), ("pc", "Post cache", "db"),
                    ("r", "Reader", "person"), ("fs", "Feed service", "focus"), ("job", "Cleanup job", "container"),
                    ("tl", "Timeline cache", "db")]:
    s.part(pid, lab, k)
s.msg("a", "pdb", "DELETE post: one write to the source of truth", hl=True)
s.msg("pdb", "pc", "CDC: invalidate the post", "async")
s.msg("r", "fs", "open feed")
s.msg("fs", "fs", "drop authors I block or unfollowed (small set)")
s.msg("fs", "pc", "hydrate")
s.ret("pc", "fs", "miss: deleted, so dropped", hl=True)
s.msg("job", "tl", "later: remove stale IDs (cosmetic)", "async")
s.save(OUT / "seq-delete.svg")

# ── Sequence: timeline shard lost, rebuild by pull ───────────────────────────────────────────────
s = seq()
for pid, lab, k in [("r", "Readers", "person"), ("fs", "Feed service", "focus"), ("tl", "Timeline cache", "db"),
                    ("ai", "Author indexes", "db"), ("rl", "Rebuild limiter", "container")]:
    s.part(pid, lab, k)
s.msg("r", "fs", "open feed")
s.msg("fs", "tl", "get timeline")
s.ret("tl", "fs", "empty: shard lost")
s.msg("fs", "rl", "rebuild token? (coalesce same user)", hl=True)
s.frame("alt", "token granted")
s.msg("fs", "ai", "followees' recent posts, merged")
s.msg("fs", "tl", "write the rebuilt timeline back")
s.end()
s.frame("alt", "rebuild capacity exhausted")
s.ret("fs", "r", "degraded feed: celebrities + recent", hl=True)
s.end()
s.save(OUT / "seq-rebuild.svg")

# ── Mid-round: the 48-hour chronological catch-up ────────────────────────────────────────────────
d = c4.Diagram(1600, 600)
d.node("r", 40, 160, 260, 150, "person", "Reader", "Person", "catch up on 48 hours")
d.node("fs", 420, 140, 320, 190, "focus", "Catch-up endpoint", "new, in the feed service", "chronological, not ranked")
d.node("ai", 880, 60, 320, 150, "db", "Author indexes", "source of truth", "followees, last 48 h")
d.node("cc", 880, 290, 320, 150, "db", "Per-user result cache", "minutes", "")
d.node("tl", 1300, 160, 260, 150, "ext", "Timeline cache", "untouched", "bounded and ranked")
d.edge("r", "fs", "", src="r:0.5", dst="l:0.5")
d.edge("fs", "ai", "merge", "", src="r:0.3", dst="l:0.5", at=(810, 150), width=70)
d.edge("fs", "cc", "cache", "", src="r:0.7", dst="l:0.5", at=(810, 330), width=70)
d.note(40, 480, 1520, "The same pull path that rebuilds lost timelines. A heavier read for an occasional feature: "
       "say the cost aloud.", size=22, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "midround-48h.svg")

# ── EM: phasing ──────────────────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
ph = [("a", "Phase 1", "pure pull + caching", "enough at today's scale; one moving part", "container"),
      ("b", "Phase 2", "push for active users", "when read cost or latency says so", "container"),
      ("c", "Phase 3", "the celebrity split", "when the first account crosses the threshold", "focus")]
for i, (nid, t, h, desc, k) in enumerate(ph):
    d.node(nid, 40 + i * 520, 70, 470, 220, k, h, t, desc, size=27)
for a, b in zip("ab", "bc"):
    d.edge(a, b, "", src="r", dst="l", dashed=False)
d.note(40, 350, 1520, "Each step is triggered by a measured number, not by the diagram. On-call watches freshness "
       "from day one.", size=22, colour=GREEN, bg=GREEN_BG)
d.save(OUT / "em-phases.svg")

# ── Follow-up 1: the ranking team wants 300 ms ───────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
op = [("a", "Say yes", "300 ms in the path", "p99 breaks for everyone; app opens feel slow", "ext"),
      ("b", "Pre-rank", "on app background", "the new model runs before the open, off the path", "focus"),
      ("c", "Two-stage", "cheap first, heavy on top 50", "heavy model sees fewer items, within budget", "container"),
      ("d", "Experiment", "1% holdout, then decide", "engagement against latency, one owner signs off", "container")]
for i, (nid, h, t, desc, k) in enumerate(op):
    d.node(nid, 40 + i * 390, 70, 350, 250, k, h, t, desc, size=24)
d.note(40, 380, 1520, "The budget is a product decision with a number on it. Bring the latency cost and "
       "the engagement data; let the product owner choose.", size=21, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "fu-ranking.svg")

# ── Follow-up 2: the incident ────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
tl = [("a", "0–5 min", "detect", "empty-feed rate pages on-call", "focus"),
      ("b", "5–15 min", "contain", "degraded feed on; rebuild rate capped", "container"),
      ("c", "15–60 min", "recover", "replace the shard; rebuild by pull, coalesced", "container"),
      ("d", "next week", "learn", "blameless review; game day; warm standby?", "container")]
for i, (nid, t, h, desc, k) in enumerate(tl):
    d.node(nid, 40 + i * 390, 70, 350, 240, k, h, t, desc, size=25)
for a, b in zip("abc", "bcd"):
    d.edge(a, b, "", src="r", dst="l", dashed=False)
d.note(40, 370, 1520, "No data is lost: timelines are rebuildable. The risk is the author index melting under "
       "the stampede, so the limiter matters more than the fix.", size=21, colour=RED, bg=RED_BG)
d.save(OUT / "fu-incident.svg")

# ── Follow-up 3: pull to hybrid in one quarter ───────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
mg = [("a", "Weeks 1–3", "dual write", "fan-out runs in shadow; timelines fill"),
      ("b", "Weeks 4–6", "compare", "read both, serve pull; diff the top 50"),
      ("c", "Weeks 7–9", "ramp", "1% → 10% → 100% serve from timelines"),
      ("d", "Weeks 10–13", "celebrity split", "threshold on; pull path kept for rebuilds")]
for i, (nid, t, h, desc) in enumerate(mg):
    d.node(nid, 40 + i * 390, 70, 350, 240, "focus" if i == 3 else "container", h, t, desc, size=25)
for a, b in zip("abc", "bcd"):
    d.edge(a, b, "", src="r", dst="l", dashed=False)
d.note(40, 370, 1520, "Two teams: fan-out and timelines; feed serving. The contract between them is the timeline "
       "schema, agreed in week one. Every step reversible by a flag.", size=21, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "fu-migration.svg")

# ── Follow-up 4: the RAM bill ────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
lv = [("a", "Slice first", "what grew?", "users, entries per user, or bytes per entry"),
      ("b", "Inactive users", "biggest lever", "no fan-out, evict their timelines"),
      ("c", "Shorter lists", "500 → 300", "measure scroll depth first"),
      ("d", "Smaller rows", "IDs only", "audit for bodies creeping in")]
for i, (nid, h, t, desc) in enumerate(lv):
    d.node(nid, 40 + i * 390, 70, 350, 240, "focus" if i == 1 else "container", h, t, desc, size=25)
d.note(40, 370, 1520, "Report cost per daily active user, not the total. Forecast it with finance each quarter.",
       size=22, colour=GREEN, bg=GREEN_BG)
d.save(OUT / "fu-cost.svg")

# ════════ v2 (2026-10-29): Staff L6/L7 depth ════════
# ── Load funnel with the arithmetic ──────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
L = [("f1", "~75 k reads/s", "feed opens, peak", "500 M DAU × 5 opens ÷ 10⁵ s × 3 peak"),
     ("f2", "~600 posts/s", "writes", "500 M × 0.1 posts/day ÷ 86,400"),
     ("f3", "~120 k inserts/s", "timeline fan-out", "600 posts/s × 200 followers"),
     ("f4", "~60 k inserts/s", "after skipping inactive", "≈ half of followers idle 30+ days"),
     ("f5", "~5–20 reads", "per open, celebrity lists", "followed celebrities, one small list each"),
     ("f6", "50 hydrations", "per open, multi-get", "top 50 of ~200 candidates")]
for i, (nid, h, t, desc) in enumerate(L):
    x = 40 + (i % 3) * 520; y = 60 + (i // 3) * 330
    d.node(nid, x, y, 460, 230, "focus" if i in (2, 3) else "container", h, t, desc, size=25)
d.edge("f1", "f2", "", src="r", dst="l", dashed=False)
d.edge("f2", "f3", "", src="r", dst="l", dashed=False)
d.edge("f3", "f4", "", src="b:0.5", dst="t:0.5", via=[(1310, 330), (270, 330)], dashed=False)
d.edge("f4", "f5", "", src="r", dst="l", dashed=False)
d.edge("f5", "f6", "", src="r", dst="l", dashed=False)
d.note(40, 680, 1520, "Writes are small; fan-out multiplies them 200×; skipping inactive users halves that. Reads stay "
       "cache-only: one timeline, a handful of celebrity lists, one multi-get.", size=20, colour=GREEN, bg=GREEN_BG)
d.save(OUT / "load-funnel.svg")

# ── Redis key space: how the keys reference each other ───────────────────────────────────────────
d = ERD(1600, 760, size=22)
d.entity("tl", 20, 20, 480, "timeline:{u}   ZSET", [("member", "postId·authorId 16 B", ""), ("score", "ts ms (8 B double)", ""),
         ("size", "≤ 500 · trim by rank", "")], kind="focus", caption="one per active user")
d.entity("pc", 1080, 20, 500, "post:{id}   HASH", [("author", "user id", ""), ("text", "≤ 2 KB", ""),
         ("media", "CDN URLs", ""), ("deleted", "0 | 1", "")], kind="redis", caption="hydration cache: MGET 50 at a time")
d.entity("cf", 20, 340, 480, "celebsFollowed:{u}   SET", [("member", "celebrity author id", ""), ("size", "typically 5–20", "")],
         kind="redis", caption="which celebrity lists to merge")
d.entity("ce", 660, 340, 400, "celeb:{a}   LIST", [("item", "postId", ""), ("size", "last ~100 · LTRIM", ""),
         ("replicas", "read from any of N", "")], kind="redis", caption="one per celebrity author")
d.entity("bl", 660, 610, 400, "hide:{u}   SET", [("member", "blocked / unfollowed id", "")], kind="redis",
         caption="subtracted from candidates")
d.entity("ls", 1080, 610, 500, "lastSeen:{u}   STRING", [("value", "epoch day", "")], kind="redis",
         caption="read by fan-out to skip the idle")
d.rel("tl", "pc", "N", "1", src="r:0.38", dst="l:0.33", label="member → post:{postId}", at=(790, 96))
d.rel("cf", "ce", "N", "1", src="r:0.45", dst="l:0.4", label="→ celeb:{a}", at=(580, 385))
d.rel("ce", "pc", "N", "1", src="r:0.3", dst="b:0.3", via=[(1230, 400)], label="item → post:{id}", at=(1230, 320))
d.rel("bl", "ce", "", "", src="t:0.5", dst="b:0.5", label="filters", dashed=True, at=(860, 575))
d.note(20, 560, 520, "Read path follows the arrows: timeline → post; celebsFollowed → celeb → post. hide removes "
       "authors from both.", size=19, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "redis-keys.svg")

# ── Where each Redis key comes from ──────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
W = [("fo", 30, 230, "Fan-out worker", "consumer of PostCreated", "branches on authorTier"),
     ("pf", 300, 100, "Post-cache filler", "in the feed service", "read-through on a miss"),
     ("gc", 430, 230, "Graph-change consumer", "FollowChanged · BlockChanged", "from the social graph's log"),
     ("st", 680, 100, "Session tracker", "on every app open", "")]
for nid, y, h, t, ty, ds in W:
    d.node(nid, 40, y, 440, h, "container" if nid != "fo" else "focus", t, ty, ds, size=21)
K = [("k1", 30, "timeline:{u}"), ("k2", 160, "celeb:{a}"), ("k3", 300, "post:{id}"),
     ("k4", 430, "celebsFollowed:{u}"), ("k5", 560, "hide:{u}"), ("k6", 680, "lastSeen:{u}")]
for nid, y, t in K:
    d.node(nid, 1100, y, 460, 100, "db", t, "Redis", "", size=21)
for a_, b_, lab, ya, yb in [("fo", "k1", "ZADD, trim to 500 · NORMAL / MID", 0.25, 0.5), ("fo", "k2", "LPUSH, LTRIM 100 · CELEB", 0.75, 0.5),
                            ("pf", "k3", "HSET on miss · DEL on CDC", 0.5, 0.5), ("gc", "k4", "SADD / SREM if followee is CELEB", 0.28, 0.5),
                            ("gc", "k5", "SADD on block or unfollow", 0.78, 0.5), ("st", "k6", "SET today's epoch day", 0.5, 0.5)]:
    y0 = dict((w[0], w) for w in W)[a_]; yk = dict((k[0], k) for k in K)[b_]
    d.edge(a_, b_, lab, "", src=f"r:{ya}", dst=f"l:{yb}", at=(790, yk[1] + 50 - 14), width=440)
d.save(OUT / "redis-writers.svg")

# ── ERD: posts, author index, graph ──────────────────────────────────────────────────────────────
d = ERD(1600, 820, size=22)
d.entity("p", 20, 20, 500, "posts", [("post_id", "bigint (Snowflake)", "PK"), ("author_id", "bigint", "IX"),
         ("text", "text", ""), ("media_ids", "bigint[]", ""), ("visibility", "smallint", ""),
         ("created_at", "timestamp", ""), ("deleted_at", "timestamp", "")], kind="focus",
         caption="sharded by post_id; time-sortable ID")
d.entity("ai", 600, 20, 470, "author_posts", [("author_id", "bigint", "PK"), ("created_at", "timestamp desc", "PK"),
         ("post_id", "bigint", "FK")], caption="wide-column: partition author_id, cluster time")
d.entity("fo", 600, 320, 470, "followers", [("followee_id", "bigint", "PK"), ("follower_id", "bigint", "PK"),
         ("since", "timestamp", "")], caption="paged by fan-out workers")
d.entity("fe", 1150, 320, 440, "followees", [("follower_id", "bigint", "PK"), ("followee_id", "bigint", "PK"),
         ("is_celebrity", "bool (cached)", "")], caption="both directions stored")
d.entity("u", 1150, 20, 440, "accounts", [("user_id", "bigint", "PK"), ("follower_count", "int", ""),
         ("tier", "normal | mid | celeb", ""), ("last_seen_day", "int", "")], caption="tier drives fan-out")
d.rel("p", "ai", "1", "1", src="r:0.2", dst="l:0.4", label="post_id")
d.rel("u", "fo", "1", "N", src="b:0.3", dst="r:0.3", via=[(1282, 280), (1110, 280), (1110, 390)], label="followee", at=(1110, 300))
d.rel("u", "fe", "1", "N", src="b:0.7", dst="t:0.7", label="follower")
d.note(20, 620, 1570, "Snowflake ID = 41 bits ms timestamp · 10 bits machine · 12 bits sequence: sortable by time without "
       "a lookup, so a timeline can order by ID. Posts are the only source of truth; timelines and lists are derived and "
       "rebuildable.", size=20)
d.save(OUT / "erd.svg")

# ════════ v3 (2026-10-29, the author's review of v2): terms, Chen ERD, wide-column, outbox/CDC, routing ════════
from erdsvg import Chen
# ── Glossary: fan-out on write (push) against fan-in on read (pull) ──────────────────────────────
d = c4.Diagram(1600, 700)
d.text(40, 40, "Fan-out on write (push): work when a post is made", size=26, colour="#c8341f", bold=True)
d.text(840, 40, "Fan-in on read (pull): work when a feed is opened", size=26, colour="#1168bd", bold=True)
d.node("au", 40, 230, 260, 150, "person", "Author", "posts once", "")
for i, nm in enumerate(["Follower A", "Follower B", "Follower C"]):
    d.node(f"t{i}", 470, 80 + i * 170, 290, 130, "db", f"{nm}'s timeline", "precomputed", "", size=20)
    d.edge("au", f"t{i}", "", src="r:0.5", dst="l:0.5", dashed=False)
d.node("rd", 1300, 230, 260, 150, "person", "Reader", "opens the feed", "")
for i, nm in enumerate(["Author X", "Author Y", "Author Z"]):
    d.node(f"a{i}", 840, 80 + i * 170, 290, 130, "db", f"{nm}'s posts", "author index", "", size=20)
    d.edge(f"a{i}", "rd", "", src="r:0.5", dst="l:0.5", dashed=False)
d.note(40, 600, 720, "Cost grows with the author's followers. Reads are one lookup.", size=21, colour=RED, bg=RED_BG)
d.note(840, 600, 720, "Cost grows with the reader's followees. Writes are one append.", size=21, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "push-pull.svg")

# ── The tail: followers per account, log scale ───────────────────────────────────────────────────
d = ERD(1600, 640, size=22)
bars = [("median account", 200, "~200 followers", "#2f6fb5"), ("top 1%", 10_000, "~10 k", "#2f6fb5"),
        ("top 0.01%", 1_000_000, "~1 M", "#a86a12"), ("the largest", 100_000_000, "100 M+", "#c8341f")]
import math
X0, SC = 330, 140
d.text(40, 50, "Followers per account · log scale · illustrative", size=24, colour="#57606a", bold=True)
for i, (lab, n, val, col) in enumerate(bars):
    y = 100 + i * 105; w = math.log10(n) * SC
    d.text(310, y + 48, lab, size=24, colour="#1f2328", bold=True, anchor="end")
    d.raw(f'<rect x="{X0}" y="{y + 12}" width="{w:.0f}" height="56" rx="6" fill="{col}"/>')
    d.text(X0 + w + 14, y + 50, val, size=24, colour=col, bold=True)
for k in range(0, 9, 2):
    x = X0 + k * SC
    d.raw(f'<line x1="{x:.0f}" y1="90" x2="{x:.0f}" y2="520" stroke="#d0d7de" stroke-dasharray="4 4"/>')
    d.text(x, 545, f"10^{k}" if k else "1", size=18, anchor="middle")
d.note(40, 570, 1520, "One post's push cost = its author's followers. The few accounts on the right decide the design.",
       size=21, colour=RED, bg=RED_BG)
d.save(OUT / "tail.svg")

# ── Conceptual ERD, Chen notation ────────────────────────────────────────────────────────────────
d = Chen(1600, 860, size=22)
d.entity("u", 480, 400, "USER", w=240)
d.entity("p", 1180, 400, "POST", w=240)
d.entity("t", 1180, 740, "TIMELINE ENTRY", weak=True, w=300)
d.rel("au", 830, 400, "AUTHORS")
d.rel("fo", 480, 715, "FOLLOWS", w=220)
d.rel("bl", 480, 120, "BLOCKS", w=200)
d.rel("in", 820, 740, "IN FEED OF", identifying=True, w=230)
d.rel("rf", 1180, 575, "REFERENCES", w=240, h=88)
d.link("u", "au", "1", card_at=0.55)
d.link("au", "p", "N", total=True, card_at=0.45)
d.link("u", "fo", "M", src="b:0.22", role="follower", card_at=0.55, role_at=0.3)
d.link("u", "fo", "N", src="b:0.78", role="followee", card_at=0.55, role_at=0.3)
d.link("u", "bl", "M", src="t:0.22", role="blocker", card_at=0.5, role_at=0.25)
d.link("u", "bl", "N", src="t:0.78", role="blocked", card_at=0.5, role_at=0.25)
d.link("u", "in", "1", src="r:0.85", card_at=0.5)
d.link("in", "t", "N", total=True, card_at=0.5)
d.link("p", "rf", "1", card_at=0.5)
d.link("rf", "t", "N", total=True, card_at=0.5)
for aid, cx, cy, lab, kw in [("uid", 175, 245, "user_id", dict(key=True)), ("uh", 150, 335, "handle", {}),
                             ("ut", 150, 425, "tier", {}), ("ufc", 760, 240, "follower_count", dict(derived=True))]:
    d.attr(aid, cx, cy, lab, of="u", **kw)
d.attr("uls", 190, 525, "last_seen_day", of="u")
for aid, cx, cy, lab, kw in [("pid", 1040, 230, "post_id", dict(key=True)), ("pm", 1330, 230, "media_ids", dict(multi=True)),
                             ("ptx", 1470, 330, "text", {}), ("pca", 1470, 430, "created_at", {}), ("pdl", 1470, 530, "deleted_at", {})]:
    d.attr(aid, cx, cy, lab, of="p", **kw)
d.attr("tpk", 1470, 700, "post_id", of="t", partial=True)
d.attr("tsc", 1470, 800, "score (ts)", of="t")
d.attr("fs", 720, 820, "since", of="fo")
d.legend(20, 628, size=17, gap=26)
d.save(OUT / "erd-chen.svg")

# ── Wide-column: what a partition is, and why the author index is one ─────────────────────────────
d = ERD(1600, 820, size=22)
d.text(40, 44, "author_posts · partition key = author_id (which node) · clustering key = created_at DESC (order inside)",
       size=22, colour="#1f2328", bold=True, mono=False)
nodes = [("Node A", [("48213", True), ("90017", False)]), ("Node B", [("31", False), ("777001", False)]),
         ("Node C", [("5120", False), ("66", False)])]
for i, (nm, parts) in enumerate(nodes):
    x = 40 + i * 520
    d.raw(f'<rect x="{x}" y="80" width="480" height="560" rx="12" fill="#f6f8fa" stroke="#8c959f" stroke-width="1.6"/>')
    d.text(x + 20, 116, nm, size=22, colour="#57606a", bold=True)
    for j, (aid, hot) in enumerate(parts):
        y = 140 + j * 245; col = "#c8341f" if hot else "#1168bd"
        d.raw(f'<rect x="{x + 20}" y="{y}" width="440" height="225" rx="8" fill="#ffffff" stroke="{col}" stroke-width="{3 if hot else 1.4}"/>')
        d.raw(f'<rect x="{x + 20}" y="{y}" width="440" height="40" rx="8" fill="{col}"/>')
        d.text(x + 36, y + 28, f"partition: author_id = {aid}", size=19, colour="#ffffff", bold=True, mono=True)
        rows = ["10:00:05 → 17905512…", "09:41:12 → 17905433…", "08:02:47 → 17905029…", "…older, newest first"]
        for k, r in enumerate(rows):
            d.text(x + 40, y + 74 + k * 40, r, size=19, colour="#1f2328" if k < 3 else "#8c959f", mono=True)
d.note(40, 660, 1520, "Query: author 48213's posts since 48 h ago = one partition on one node, one sequential read in "
       "time order. A row store does the same with an index on (author_id, created_at); a wide-column store makes that "
       "layout the table itself, and spreads partitions over nodes by hash.", size=20, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "wide-column.svg")

# ── Sequence: transactional outbox, carried by CDC ───────────────────────────────────────────────
s = seq(size=21, row=52)
for pid, lab, k in [("ps", "Post service", "container"), ("db", "Posts DB (posts + outbox)", "db"),
                    ("cdc", "CDC connector", "container"), ("log", "Post-created log", "queue"),
                    ("fo", "Fan-out workers", "focus"), ("ot", "Search · notifications", "ext")]:
    s.part(pid, lab, k)
s.msg("ps", "db", "BEGIN · INSERT posts row")
s.msg("ps", "db", "INSERT outbox row (PostCreated) · COMMIT", hl=True)
s.ret("db", "ps", "committed: both rows or neither")
s.msg("db", "cdc", "commit log (WAL / binlog) streams the outbox insert", "async")
s.msg("cdc", "log", "publish PostCreated, key = authorId", hl=True)
s.msg("log", "fo", "consumer group: fan-out")
s.msg("log", "ot", "consumer groups: search, notifications")
s.note("ps", "log", "No dual write. Rollback: no event. CDC crash: resume from its log position, at least once.", "green")
s.save(OUT / "seq-outbox.svg")

# ── Fan-out routing on authorTier ────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.node("lg", 40, 300, 280, 150, "queue", "Post-created log", "key = authorId", "", size=21)
d.node("wk", 420, 285, 320, 180, "focus", "Fan-out worker", "Container", "reads authorTier from the event", size=21)
d.node("n", 860, 40, 340, 160, "container", "NORMAL", "under ~10 k followers", "push to followers active in 30 days", size=21)
d.node("m", 860, 295, 340, 160, "container", "MID", "~10 k to ~100 k", "push to followers active today", size=21)
d.node("c", 860, 550, 340, 160, "container", "CELEB", "over ~100 k", "one LPUSH; no fan-out", size=21)
d.node("tl", 1320, 160, 250, 160, "db", "timeline:{f}", "Redis", "per follower", size=21)
d.node("cl", 1320, 550, 250, 160, "db", "celeb:{a}", "Redis", "per author", size=21)
d.edge("lg", "wk", "consume", "", src="r:0.5", dst="l:0.5", at=(370, 360), width=90)
d.edge("wk", "n", "", "", src="t:0.5", dst="l:0.5", via=[(580, 120)])
d.edge("wk", "m", "", "", src="r:0.5", dst="l:0.5")
d.edge("wk", "c", "", "", src="b:0.5", dst="l:0.5", via=[(580, 630)])
d.edge("n", "tl", "ZADD", "", src="r:0.5", dst="l:0.3", at=(1260, 105), width=70)
d.edge("m", "tl", "ZADD", "", src="r:0.5", dst="l:0.75", at=(1260, 360), width=70)
d.edge("c", "cl", "LPUSH", "", src="r:0.5", dst="l:0.5", at=(1260, 615), width=80)
d.note(40, 560, 520, "The post service stamps authorTier from accounts.tier at publish. A daily job recomputes tier "
       "from follower_count, with a gap between up and down thresholds so accounts don't flap.", size=19,
       colour=BLUE, bg=BLUE_BG)
d.save(OUT / "fanout-routing.svg")

# ── Follow-up 5: the power reader ────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 560)
op = [("a", "The problem", "5,000 followees, 300 celebs", "300 list reads per open; p99 blows up"),
      ("b", "Cap the merge", "top-K by affinity", "merge the 30 celebrities they engage with most"),
      ("c", "Pre-merge", "per heavy reader", "background job folds celeb posts into their timeline"),
      ("d", "Measure", "who is affected", "~0.1% of readers; their own latency SLO")]
for i, (nid, h, t, desc) in enumerate(op):
    d.node(nid, 40 + i * 390, 70, 350, 250, "focus" if i == 2 else "container", h, t, desc, size=24)
d.note(40, 380, 1520, "The hybrid flips for heavy readers: pull is cheap per celebrity, but not for 300 of them. "
       "Treat the tail of readers like the tail of authors.", size=21, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "fu-power-reader.svg")
print("diagrams →", OUT)
