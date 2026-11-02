#!/usr/bin/env python3
"""C4, deployment, sequence and follow-up diagrams for the SD-15 distributed KV store video → ./svg/*.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg}.py.  Run: python3 diagrams.py
Content follows ../../SD-15-distributed-kv-store.md; the follow-up diagrams (fu-*) are new for this video."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq

OUT = pathlib.Path(__file__).resolve().parent / "svg"
OUT.mkdir(exist_ok=True)
GREEN, GREEN_BG, RED, RED_BG, BLUE, BLUE_BG = "#2d8a4e", "#e7f4ec", "#c8341f", "#fdecea", "#2f6fb5", "#e8f0fa"

def seq(size=22, row=50):
    return sq.Seq(1500, size=size, row=row, head=66)

def row_of(name, items, note=None, tone=(BLUE, BLUE_BG), arrows=False, focus=None, h=560):
    d = c4.Diagram(1600, h)
    n = len(items); w = (1520 - (n - 1) * 40) // n
    for i, (t, ty, desc) in enumerate(items):
        k = "focus" if (i == focus or (isinstance(focus, tuple) and i in focus)) else "container"
        d.node(f"n{i}", 40 + i * (w + 40), 70, w, 240, k, t, ty, desc, size=25 if n > 3 else 27)
    if arrows:
        for i in range(n - 1):
            d.edge(f"n{i}", f"n{i+1}", "", src="r", dst="l", dashed=False)
    if note:
        d.note(40, 370, 1520, note, size=21, colour=tone[0], bg=tone[1])
    d.save(OUT / f"{name}.svg")

# ── C4 level 1: system context ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
d.node("svc", 40, 60, 340, 170, "person", "Application services", "in 5 regions",
       "1 M reads/s, 100 k writes/s; pick a consistency per call")
d.node("ops", 40, 470, 340, 150, "person", "Platform SRE", "Person", "placement, failover, capacity")
d.node("kv", 620, 240, 380, 220, "focus", "Global KV store", "Software System",
       "10 B keys, 100 TB; local reads, homed writes")
d.node("net", 1240, 60, 320, 170, "ext", "Inter-region network", "External", "60–220 ms round trips across continents")
d.node("cloud", 1240, 470, 320, 150, "ext", "Five cloud regions", "External", "3 zones each")
d.edge("svc", "kv", "get, put, cas", "SDK", src="r:0.5", dst="l:0.25", at=(500, 160), width=140)
d.edge("ops", "kv", "policies, runbooks", "", src="r:0.5", dst="l:0.8", at=(500, 520), width=170)
d.edge("kv", "net", "replicate", "", src="r:0.2", dst="l:0.5", at=(1120, 150), width=100)
d.edge("kv", "cloud", "runs in", "", src="r:0.8", dst="l:0.5", at=(1120, 530), width=90)
d.legend(40, 735, ("person", "focus", "ext"))
d.save(OUT / "c4-context.svg")

# ── C4 level 2: containers ───────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.boundary(250, 20, 1330, 760, "Global KV store")
d.node("app", 20, 300, 200, 150, "person", "Service", "caller")
d.node("sdk", 300, 280, 260, 190, "container", "Client SDK + router", "library", "caches placement; picks a replica")
d.node("dir", 300, 560, 260, 160, "focus", "Placement directory", "consensus group", "range → home, replicas, leader")
d.node("lead", 680, 60, 360, 170, "container", "Home-region Raft group", "3 zones", "linearizable writes, 2–5 ms quorum")
d.node("fol", 680, 330, 360, 170, "container", "Async followers", "every other region", "local reads; region-loss durability")
d.node("ctl", 680, 590, 360, 150, "container", "Placement controller", "Container", "split, merge, re-home, residency")
d.node("eng", 1140, 190, 380, 170, "db", "Storage engine", "LSM per node", "versions + commit timestamps (HLC)")
d.edge("app", "sdk", "", src="r:0.5", dst="l:0.5")
d.edge("sdk", "lead", "strong write", "", src="t:0.6", dst="l:0.5", via=[(456, 145)], at=(560, 130), width=130)
d.edge("sdk", "fol", "local read", "", src="r:0.5", dst="l:0.5", at=(620, 375), width=100)
d.edge("sdk", "dir", "lookup, cached", "", src="b:0.5", dst="t:0.5", at=(430, 515), width=150)
d.edge("lead", "fol", "log, async", "", src="b:0.5", dst="t:0.5", at=(860, 280), width=110)
d.edge("lead", "eng", "", src="r:0.5", dst="l:0.3")
d.edge("fol", "eng", "", src="r:0.5", dst="l:0.8")
d.edge("ctl", "dir", "update", "", src="l:0.5", dst="r:0.5", at=(620, 655), width=80)
d.save(OUT / "c4-containers.svg")

# ── C4 level 3: inside a storage node ────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
d.boundary(240, 20, 1020, 720, "Storage node", "Container")
d.node("cl", 20, 80, 190, 140, "container", "SDK / peers", "")
d.node("rpc", 300, 70, 400, 150, "component", "RPC server", "Component", "get, put, forward to leader")
d.node("rm", 800, 70, 400, 150, "focus", "Range replica manager", "Raft per range", "terms, commit index, leases")
d.node("at", 300, 300, 400, 150, "component", "Applied-timestamp tracker", "Component", "serves bounded and session reads")
d.node("lsm", 800, 300, 400, 150, "component", "LSM engine", "RocksDB-class", "versions per key")
d.node("snap", 800, 520, 400, 150, "component", "Snapshot sender", "Component", "bootstrap followers, throttled")
d.node("fen", 300, 520, 400, 150, "component", "Fencing check", "Component", "reject writes from a stale term")
d.node("peer", 1340, 300, 230, 150, "container", "Other replicas", "")
d.edge("cl", "rpc", "", src="r:0.5", dst="l:0.5")
d.edge("rpc", "rm", "write", "", src="r:0.5", dst="l:0.5", at=(750, 125), width=60)
d.edge("rpc", "at", "read", "", src="b:0.5", dst="t:0.5", at=(500, 260), width=60)
d.edge("rm", "lsm", "apply", "", src="b:0.5", dst="t:0.5", at=(1000, 260), width=70)
d.edge("rm", "peer", "replicate", "", src="r:0.5", dst="t:0.5", via=[(1455, 145)], at=(1330, 130), width=100)
d.edge("at", "lsm", "", src="r:0.5", dst="l:0.5")
d.edge("snap", "peer", "", src="r:0.5", dst="b:0.5", via=[(1455, 595)])
d.edge("fen", "lsm", "", src="r:0.5", dst="l:0.7", via=[(750, 595), (750, 405)])
d.save(OUT / "c4-component-node.svg")

# ── Deployment: one range across five regions ────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.boundary(40, 40, 760, 420, "us-east · home of range R1", "3 zones")
d.node("l", 80, 130, 210, 150, "focus", "R1 leader", "zone a")
d.node("fb", 320, 130, 210, 150, "container", "R1 replica", "zone b")
d.node("fc", 560, 130, 210, 150, "container", "R1 replica", "zone c")
d.note(80, 330, 690, "Majority of 3 inside one region: ~2–5 ms, survives a zone loss.", size=19,
       colour=GREEN, bg=GREEN_BG)
regions = [("uw", "us-west"), ("eu", "eu-west"), ("as", "ap-south"), ("an", "ap-northeast")]
for i, (rid, name) in enumerate(regions):
    d.node(rid, 880 + (i % 2) * 360, 60 + (i // 2) * 230, 320, 170, "container", "R1 async follower", name,
           "local reads", size=22)
d.node("dir", 40, 580, 760, 170, "db", "Placement directory", "consensus, cached everywhere",
       "R1 = [k0, k1): home us-east; replicas a, b, c; followers uw, eu, as, an", size=22)
d.note(880, 520, 680, "Each follower applies R1's log asynchronously: 100–300 ms behind.", size=19)
d.save(OUT / "c4-deployment.svg")

# ── Sequence: a strong write from Tokyo ──────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("c", "Client · Tokyo", "person"), ("n", "Nearest node · Tokyo", "container"),
                    ("l", "R1 leader · us-east", "focus"), ("z", "Zones b, c · us-east", "container"),
                    ("f", "Followers · 4 regions", "container")]:
    s.part(pid, lab, k)
s.msg("c", "n", "put(k, v, strong)")
s.msg("n", "l", "forward: ~150 ms round trip", hl=True)
s.msg("l", "z", "append, replicate")
s.ret("z", "l", "majority: ~2 ms")
s.ret("l", "c", "ack {version, commitTs}: ~220 ms total", hl=True)
s.msg("l", "f", "apply the log, async: 100–300 ms", "async")
s.note("c", "f", "Strong writes are fast for clients near the home, and honest about the rest.", "amber")
s.save(OUT / "seq-strong-write.svg")

# ── Sequence: reads at three consistency levels ──────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("c", "Client · Tokyo", "person"), ("f", "Follower · Tokyo", "focus"),
                    ("l", "Leader · us-east", "container")]:
    s.part(pid, lab, k)
s.frame("alt", "eventual")
s.msg("c", "f", "get(k, eventual)")
s.ret("f", "c", "value, maybe stale: < 10 ms", hl=True)
s.end()
s.frame("alt", "bounded(5 s)")
s.msg("c", "f", "get(k, bounded 5 s)")
s.msg("f", "f", "applied within 5 s? then serve")
s.msg("f", "l", "else forward (or wait briefly)")
s.end()
s.frame("alt", "strong")
s.msg("c", "l", "get(k, strong): read at the leader, ~150 ms")
s.end()
s.save(OUT / "seq-reads.svg")

# ── Sequence: read-your-writes across regions ────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("c", "Client", "person"), ("f", "Follower · eu-west", "focus"),
                    ("l", "Leader · us-east", "container")]:
    s.part(pid, lab, k)
s.msg("c", "l", "put(k, v)")
s.ret("l", "c", "commitTs = T: the session token", hl=True)
s.msg("c", "f", "get(k, session T)")
s.msg("f", "f", "applied up to T? wait 100–300 ms, or forward", hl=True)
s.ret("f", "c", "your own write, never older")
s.save(OUT / "seq-session.svg")

# ── The consistency menu ─────────────────────────────────────────────────────────────────────────
row_of("tiers", [("Strong", "leader read", "linearizable; cross-continent cost"),
                 ("Bounded", "≤ N seconds old", "local unless the follower lags"),
                 ("Session", "commitTs token", "read your own writes anywhere"),
                 ("Eventual", "any follower", "always available, < 10 ms")],
       note="Callers choose per operation, and pay for what they ask for. Each tier gets its own SLO.",
       focus=0)

# ── The 30-second partition ──────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 660)
d.boundary(40, 40, 680, 470, "US side")
d.boundary(880, 40, 680, 470, "EU side")
d.node("uw", 80, 110, 600, 130, "focus", "US-homed keys: writes normal", "quorum is local")
d.node("ur", 80, 290, 600, 130, "container", "EU-homed keys: strong writes fail", "eventual reads go stale")
d.node("ew", 920, 110, 600, 130, "focus", "EU-homed keys: writes normal", "quorum is local")
d.node("er", 920, 290, 600, 130, "container", "US-homed keys: strong writes fail", "eventual reads go stale")
d.note(40, 550, 1520, "We chose C, for the cross-homed fraction only. After healing, followers catch up from the "
       "leaders' logs: no conflicts, because each key had one writer.", size=20, colour=GREEN, bg=GREEN_BG)
d.save(OUT / "partition.svg")

# ── Sequence: home region lost ───────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("l", "us-east (lost)", "ext"), ("eu", "Follower · eu-west", "container"),
                    ("ctl", "Placement controller", "focus"), ("dir", "Directory", "db"), ("c", "Clients", "person")]:
    s.part(pid, lab, k)
s.msg("l", "l", "region unreachable")
s.ret("eu", "ctl", "applied up to T-300 ms")
s.msg("ctl", "ctl", "pick the most up-to-date follower region", hl=True)
s.msg("ctl", "dir", "R1 home := eu-west; new Raft group")
s.msg("dir", "c", "placement changed", "async")
s.note("l", "c", "Async tail: the last few hundred ms of acknowledged writes can be lost. RPO > 0, said aloud.", "red")
s.save(OUT / "seq-failover.svg")

# ── Hot key options ──────────────────────────────────────────────────────────────────────────────
row_of("hotkey", [("Push back", "the access pattern", "it is usually a counter"),
                  ("Split", "sub-keys", "sum on read"),
                  ("CRDT counter", "eventual mode", "merge, never lose an increment"),
                  ("Combine", "at the leader", "batch writes into one log entry")],
       note="A single linearizable key has a single-leader throughput ceiling, by design. Say so.",
       tone=(RED, RED_BG), focus=1)

# ── Mid-round: residency ─────────────────────────────────────────────────────────────────────────
row_of("residency", [("Tag the range", "prefix or attribute", "EU-resident data"),
                     ("Place it", "a policy", "home eu-west; every replica in the EU"),
                     ("Forward reads", "from outside", "pay the latency; no local copy")],
       note="Range placement makes residency a policy. A consistent-hash ring places by hash, not by policy, "
            "and can't do this.", arrows=True, focus=1)

# ── EM: phasing ──────────────────────────────────────────────────────────────────────────────────
row_of("em-phases", [("Buy first", "phase 0", "managed global tables cover most of this"),
                     ("Build the core", "if needed", "single-region Raft ranges, directory, SDK"),
                     ("Go global", "then", "async followers, tiers, failover, residency")],
       note="Build only if placement control or cost demands it. The one-way doors: the partitioning scheme "
            "and the consistency contract in the API.", tone=(GREEN, GREEN_BG), arrows=True, focus=0)

# ── Follow-ups ───────────────────────────────────────────────────────────────────────────────────
row_of("fu-buy", [("Requirements", "the must-haves", "residency, tiers, RPO, scale"),
                  ("Total cost", "3 years", "licence or bill vs ~a team of engineers"),
                  ("Exit cost", "lock-in", "API, data export, migration"),
                  ("Recommend", "with a review date", "buy, and revisit at a named trigger")],
       note="Engineering effort is a cost too. A home-grown database is a decade-long commitment.", focus=3)
row_of("fu-failover", [("Detect", "0–5 min", "write availability by home region pages"),
                       ("Decide", "who and when", "named owner; RPO trade, not a reflex"),
                       ("Fail over", "per range", "promote the freshest follower region"),
                       ("Reconcile", "after", "report the lost tail; game day")],
       note="Writing to EU-homed keys never stopped. Only us-east-homed strong writes waited.",
       tone=(RED, RED_BG), arrows=True, focus=1)
row_of("fu-defaults", [("Default", "session", "read-your-writes, local and fast"),
                       ("Opt in", "strong", "per table, with its latency shown"),
                       ("Show cost", "in the SDK", "latency by client and home region"),
                       ("Review", "quarterly", "which tables pay for strong, and why")],
       note="A safe default with a visible price beats a blanket rule. The product team keeps the choice.",
       focus=0)
row_of("fu-egress", [("Slice", "by table", "who replicates to how many regions"),
                     ("Fewer followers", "per table", "read-replica regions as a dial"),
                     ("Compress", "the log", "batch and compress replication"),
                     ("Charge back", "to tables", "cost visible to the owners")],
       note="Replication factor and follower regions per table are the cost dials. Report cost per million writes.",
       tone=(GREEN, GREEN_BG), focus=1)
print("diagrams →", OUT)
