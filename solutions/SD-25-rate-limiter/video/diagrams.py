#!/usr/bin/env python3
"""C4, deployment, sequence and follow-up diagrams for the SD-25 rate-limiter video → ./svg/*.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg}.py.  Run: python3 diagrams.py
Content follows ../../SD-25-rate-limiter.md; the follow-up diagrams (fu-*) are new for this video."""
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
d.node("cust", 40, 60, 340, 160, "person", "API customers", "Person", "1 M requests a second; some 100× others")
d.node("ops", 40, 480, 340, 160, "person", "Support and product", "Person", "policies, exceptions, 'why was I limited?'")
d.node("api", 620, 240, 380, 220, "focus", "API platform with rate limiting", "Software System",
       "enforces per-customer, per-endpoint quotas across 500 servers")
d.node("bill", 1240, 60, 320, 160, "ext", "Billing and metering", "External System", "exact counts, separate pipeline")
d.node("mon", 1240, 480, 320, 160, "ext", "Monitoring", "External System", "SLIs, alerts, decision log")
d.edge("cust", "api", "HTTPS", "", src="r:0.5", dst="l:0.25", at=(500, 150), width=80)
d.edge("ops", "api", "policies", "", src="r:0.5", dst="l:0.8", at=(500, 540), width=90)
d.edge("api", "bill", "usage events", "async", src="r:0.2", dst="l:0.5", at=(1120, 150), width=130)
d.edge("api", "mon", "metrics", "", src="r:0.8", dst="l:0.5", at=(1120, 530), width=80)
d.legend(40, 735, ("person", "focus", "ext"))
d.save(OUT / "c4-context.svg")

# ── C4 level 2: containers ───────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.boundary(250, 20, 1330, 760, "API platform, one region")
d.node("c", 20, 300, 200, 150, "person", "Client", "")
d.node("lb", 300, 290, 220, 170, "container", "Load balancer", "")
d.node("api", 620, 240, 380, 270, "focus", "API servers × ~170", "with the limiter library",
       "token bucket per (customer, endpoint), in memory")
d.node("co", 1120, 70, 400, 170, "db", "Regional coordinator", "Redis cluster + Lua", "usage reports, shares, every 100 ms")
d.node("pol", 1120, 320, 400, 150, "container", "Policy service", "Container", "pushes changes; cached everywhere")
d.node("log", 1120, 560, 400, 150, "db", "Decision log", "sampled, columnar", "all rejections, some allows")
d.edge("c", "lb", "", src="r:0.5", dst="l:0.5")
d.edge("lb", "api", "", src="r:0.5", dst="l:0.5")
d.edge("api", "co", "report, get share", "async", src="r:0.15", dst="l:0.5", at=(1060, 140), width=150)
d.edge("pol", "api", "push", "", src="l:0.5", dst="r:0.55", at=(1060, 395), width=60)
d.edge("api", "log", "sampled", "", src="r:0.9", dst="l:0.5", via=[(1060, 483), (1060, 635)], at=(1060, 560), width=90)
d.save(OUT / "c4-containers.svg")

# ── C4 level 3: the limiter library ──────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 760)
d.boundary(240, 20, 1000, 720, "Limiter library, in each API server", "Component")
d.node("h", 20, 80, 190, 140, "container", "Request handler", "")
d.node("dec", 300, 70, 420, 150, "focus", "Decide", "Component", "take a token; set headers; 429 with Retry-After")
d.node("pc", 820, 70, 380, 150, "component", "Policy cache", "Component", "rate, burst, scope, mode, version")
d.node("bk", 300, 300, 420, 150, "component", "Local buckets", "in memory", "tokens, last refill, current share")
d.node("sm", 820, 300, 380, 150, "component", "Share manager", "every 100 ms", "report demand, receive share")
d.node("fb", 820, 520, 380, 150, "component", "Fallback", "Component", "last shares, decaying to a safe default")
d.node("smp", 300, 520, 420, 150, "component", "Decision sampler", "Component", "every 429; a sample of allows")
d.node("co", 1340, 300, 230, 150, "db", "Coordinator", "")
d.edge("h", "dec", "allow?", "", src="r:0.5", dst="l:0.5", at=(255, 125), width=70)
d.edge("dec", "pc", "", src="r:0.5", dst="l:0.5")
d.edge("dec", "bk", "", src="b:0.5", dst="t:0.5")
d.edge("bk", "sm", "", src="r:0.5", dst="l:0.5")
d.edge("sm", "co", "", src="r:0.5", dst="l:0.5")
d.edge("sm", "fb", "coordinator down", "", src="b:0.5", dst="t:0.5", at=(1010, 485), width=170)
d.edge("dec", "smp", "", src="l:0.7", dst="l:0.5", via=[(270, 175), (270, 595)])
d.save(OUT / "c4-component-limiter.svg")

# ── Deployment ───────────────────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 700)
for i, (rid, name) in enumerate([("a", "Region A"), ("b", "Region B"), ("c", "Region C")]):
    x = 40 + i * 520
    d.boundary(x, 30, 480, 450, name)
    d.node(f"s{rid}", x + 40, 100, 400, 140, "container", "~170 API servers", "limiter in-process")
    d.node(f"r{rid}", x + 40, 300, 400, 130, "focus", "Coordinator", "Redis cluster, a few shards")
    d.edge(f"s{rid}", f"r{rid}", "100 ms", "", src="b:0.5", dst="t:0.5", at=(x + 240, 270), width=80)
d.edge("ra", "rb", "", src="r:0.5", dst="l:0.5")
d.edge("rb", "rc", "", src="r:0.5", dst="l:0.5")
d.note(40, 540, 1520, "scope: region is exact per region with no cross-region traffic. scope: global exchanges totals "
       "every few seconds; overshoot is one sync interval of demand shift.", size=20, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "c4-deployment.svg")

# ── Sequence: one request on the hot path ────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("c", "Client", "person"), ("api", "API server", "container"), ("lib", "Limiter library", "focus"),
                    ("b", "Local bucket", "db"), ("h", "Handler", "container")]:
    s.part(pid, lab, k)
s.msg("c", "api", "GET /orders")
s.msg("api", "lib", "allow(customer, endpoint)")
s.msg("lib", "b", "refill, take one token: microseconds", hl=True)
s.frame("alt", "token available")
s.msg("api", "h", "handle")
s.ret("api", "c", "200 + RateLimit-Remaining, Reset")
s.end()
s.frame("alt", "bucket empty")
s.ret("api", "c", "429 + Retry-After", hl=True)
s.end()
s.note("c", "h", "No network hop on the hot path. The limiter adds well under a millisecond.", "green")
s.save(OUT / "seq-request.svg")

# ── Sequence: the share sync ─────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("s1", "Server 1", "container"), ("s2", "Server 2", "container"), ("co", "Coordinator", "focus"),
                    ("og", "Other regions", "ext")]:
    s.part(pid, lab, k)
s.frame("loop", "every ~100 ms")
s.msg("s1", "co", "used 40 for key K")
s.msg("s2", "co", "used 4 for key K")
s.msg("co", "co", "share_i = remaining × demand_i / Σ demand", hl=True)
s.ret("co", "s1", "share 90%")
s.ret("co", "s2", "share 10%")
s.end()
s.msg("co", "og", "totals for global keys, every few seconds", "async")
s.save(OUT / "seq-share.svg")

# ── Shares follow demand ─────────────────────────────────────────────────────────────────────────
row_of("shares", [("Static split", "1,000 ÷ 500 servers", "2 per server per minute: useless"),
                  ("Demand-weighted", "recomputed every 100 ms", "the busy server gets the budget"),
                  ("Error bound", "one interval of demand shift", "a few tokens; 1–2% for the heaviest")],
       note="Uneven load balancing stops mattering: shares follow traffic, not node count.",
       focus=1)

# ── Sequence: a cold key ─────────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("c", "Client", "person"), ("lib", "Limiter library", "focus"), ("co", "Coordinator", "db")]:
    s.part(pid, lab, k)
s.msg("c", "lib", "first request for key K on this server")
s.msg("lib", "co", "share for K? once, in-region, ~0.5 ms", hl=True)
s.ret("co", "lib", "share")
s.msg("lib", "lib", "cache it; later requests are local")
s.ret("lib", "c", "allow")
s.save(OUT / "seq-cold.svg")

# ── Sequence: coordinator down ───────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("c", "Clients", "person"), ("lib", "Limiter library", "focus"), ("co", "Coordinator (down)", "ext"),
                    ("on", "On-call", "person")]:
    s.part(pid, lab, k)
s.msg("lib", "co", "report usage")
s.ret("co", "lib", "timeout")
s.msg("lib", "lib", "keep last shares, decay toward a safe default", hl=True)
s.msg("c", "lib", "requests")
s.ret("lib", "c", "still enforced, roughly: API stays up", hl=True)
s.msg("lib", "on", "alert: degraded, not an outage", "async")
s.save(OUT / "seq-coord-down.svg")

# ── Sequence: policy rollout ─────────────────────────────────────────────────────────────────────
s = seq()
for pid, lab, k in [("op", "Operator", "person"), ("ps", "Policy service", "focus"), ("can", "Canary servers", "container"),
                    ("all", "All servers", "container"), ("log", "Decision log", "db")]:
    s.part(pid, lab, k)
s.msg("op", "ps", "new policy, mode: shadow")
s.msg("ps", "all", "push: would-reject counted, nothing blocked", hl=True)
s.msg("log", "op", "how many 429s would this cause?", "async")
s.msg("op", "ps", "mode: enforce")
s.msg("ps", "can", "canary first")
s.msg("ps", "all", "then everyone; rollback in seconds", hl=True)
s.save(OUT / "seq-policy.svg")

# ── Multi-region scopes ──────────────────────────────────────────────────────────────────────────
row_of("scopes", [("scope: region", "the default", "limit × regional weight; exact per region"),
                  ("scope: global", "sync every few seconds", "overshoot: one interval of cross-region shift"),
                  ("Exact global", "rejected", "~100 ms per decision; the budget is 1 ms")],
       note="Say the honest answer: an exact global limit can't fit the latency budget.", focus=1)

# ── Mid-round ────────────────────────────────────────────────────────────────────────────────────
row_of("midround-burst", [("Scheduled policy", "burst ×10 at :00–:00:30", "pushed by the policy service"),
                          ("Push back", "the cost", "special cases accumulate"),
                          ("Productise", "burst credits", "a tier, with an owner and an expiry")],
       note="Say yes to the customer and no to the hand-edited exception.", arrows=True, focus=2)

# ── EM phasing ───────────────────────────────────────────────────────────────────────────────────
row_of("em-phases", [("Week one", "local buckets", "conservative static share; shadow mode; decision log"),
                     ("Week four", "the coordinator", "demand-weighted shares, fail open"),
                     ("Later", "global scope", "only for policies that need it")],
       note="The decision log and the false-limit SLI ship in week one: the first real problem is "
            "'why was I limited?'", tone=(GREEN, GREEN_BG), arrows=True, focus=0)

# ── Follow-ups ───────────────────────────────────────────────────────────────────────────────────
row_of("fu-exempt", [("Understand", "the real need", "launch day? a batch job? a bigger tier?"),
                     ("Offer", "a higher limit", "not 'no limit': protection stays"),
                     ("Govern", "owner + expiry", "every exception reviewed"),
                     ("Escalate", "if needed", "risk written down, decided by the right owner")],
       note="An unlimited customer can take down the API for everyone else. Price the risk; don't just refuse.",
       focus=1)
row_of("fu-incident", [("Detect", "minute 1", "429 rate spikes; false-limit SLI fires"),
                       ("Roll back", "minute 3", "previous policy version, one command"),
                       ("Tell", "minute 10", "status page; support script; affected customers"),
                       ("Prevent", "next week", "shadow mode and canary become mandatory")],
       note="The fix is a process: config is code, and code ships through shadow and canary.",
       tone=(RED, RED_BG), arrows=True, focus=1)
row_of("fu-billing", [("Different jobs", "protect vs charge", "approximate is fine for one, not the other"),
                      ("Separate pipeline", "exact, async", "usage events from the log, deduplicated"),
                      ("Shared source", "one event stream", "two consumers, two guarantees")],
       note="Mixing them would force exactness onto the hot path for no reason. Name the owner of each.",
       focus=1)
row_of("fu-cost", [("Slice", "what grew?", "allows logged, rejections, retention"),
                   ("Sample allows", "1%", "keep every rejection"),
                   ("Tier retention", "hot 7 days", "cold after; aggregates kept longer"),
                   ("Keep the tool", "support works", "answer 'why' in minutes")],
       note="Cut the cost without losing the ability to explain a single 429.", tone=(GREEN, GREEN_BG), focus=1)
print("diagrams →", OUT)
