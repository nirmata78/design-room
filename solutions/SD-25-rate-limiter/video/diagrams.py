"""SD-25: the pictures that are not C4 views -> ./svg/ (sequences, the physical data model, the policy lifecycle, figures).
Every C4 view (context, containers, V1 -> V4, flows, challenge zooms, recap, alternate) comes from ../workspace.dsl +
../views.json through c4-structurizr; this file never draws a box of the architecture.
Run by ref_solution.py diagrams (which renders the C4 views first, into the same folder); never clears svg/."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]                     # the repo
sys.path.insert(0, str(ROOT / ".claude/skills/reference-solution/kit"))
import seqsvg as sq                                                     # noqa: E402
import erdsvg as er                                                     # noqa: E402
from statesvg import States                                             # noqa: E402
from figsvg import budget_bar, svgdoc, T, R, L                         # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
INK, RED, GREEN, BLUE, GREY, AMBER = "#202124", "#ea4335", "#34a853", "#4285f4", "#5f6368", "#fbbc05"


# ── sequences ──
def seq(name, parts, steps, size=24, row=54, width=1500):
    q = sq.Seq(width, size=size, row=row)
    for p in parts: q.part(*p)
    for st in steps:
        k = st[0]
        if k == "m": q.msg(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "r": q.ret(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "n": q.note(st[1], st[2], st[3], *(st[4:5]))
    q.save(OUT / f"{name}.svg")

# challenge 2: one key, two servers, two intervals — leases follow demand
seq("seq-share",
    [("a", "API server A", "container"), ("q", "Quota service, shard 3", "container"), ("b", "API server B", "container")],
    [("m", "a", "q", "sync: key 42:/search admitted 700, asked 700"),
     ("m", "b", "q", "sync: admitted 300, asked 300"),
     ("n", "q", "q", "budget 1,000 per 100 ms; split by asked, + 5 %", "blue"),
     ("r", "q", "a", "lease 735 for the next 100 ms"),
     ("r", "q", "b", "lease 315"),
     ("n", "b", "b", "traffic moves to B: asked 700, 315 admitted, 385 get 429", "amber"),
     ("m", "b", "q", "sync: admitted 315, asked 700"),
     ("m", "a", "q", "sync: admitted 200, asked 200"),
     ("r", "q", "b", "lease 815: the share followed the demand", dict(hl=True))], size=25, row=52, width=1700)

# challenge 3: the quota shard fails; leases, then the floor, then the standby
seq("seq-down",
    [("s", "API server", "container"), ("q", "Quota shard 3", "container"), ("w", "Standby shard 3", "container")],
    [("m", "s", "q", "sync: admitted, asked"),
     ("n", "q", "q", "the primary is gone: no answer in 50 ms", "amber"),
     ("n", "s", "s", "keep spending the last lease: valid 10 s", "green"),
     ("n", "s", "s", "after 10 s: floor = 3 × regional limit ÷ 167 servers", "amber"),
     ("m", "s", "w", "sync to the promoted standby: admitted, asked"),
     ("r", "w", "s", "leases again, one interval later", dict(hl=True))], size=25, row=56, width=1600)

# challenge 4: three regions re-split one global budget every 2 s
seq("seq-regions",
    [("eu", "Quota service, eu-west", "container"), ("us", "Quota service, us-east", "container"), ("ap", "Quota service, ap-south", "container")],
    [("m", "eu", "us", "every 2 s: key 7 admitted 790/s, asked 800/s", dict(kind="async")),
     ("m", "us", "eu", "admitted 150/s, asked 150/s", dict(kind="async")),
     ("m", "ap", "eu", "admitted 50/s, asked 50/s", dict(kind="async")),
     ("n", "eu", "ap", "global 1,000/s split by asked: eu 800, us 150, ap 50", "blue"),
     ("n", "us", "us", "16:00: us asks 700/s; it is held to 150 for at most 2 s", "amber"),
     ("m", "us", "eu", "admitted 150/s, asked 700/s", dict(kind="async")),
     ("n", "eu", "ap", "re-split: eu 270, us 680, ap 50", "green")], size=25, row=56, width=1700)

# ── the physical data model ──
e = er.ERD(1600, 760, size=26)
e.entity("ti", 30, 40, 470, "tier  (PostgreSQL)", [("tier_id", "text", "PK"), ("rate_per_min", "int", ""), ("burst", "int", ""),
         ("windows", "jsonb", "")], caption="about 20 tiers; most policies inherit one")
e.entity("po", 570, 40, 470, "policy  (PostgreSQL)", [("customer_id", "bigint", "PK"), ("endpoint", "text", "PK"), ("version", "int", "PK"),
         ("tier_id", "text", "FK"), ("scope · mode", "enum", ""), ("on_failure", "open | closed", ""),
         ("state", "text", "")], kind="focus", caption="a change is a new version; owner and expiry")
e.entity("de", 1110, 40, 460, "decision  (ClickHouse)", [("decision_id", "uuid", "PK"), ("ts", "ts", ""), ("customer, endpoint", "key", "IX"),
         ("allowed", "bool", ""), ("policy_v", "int", ""), ("lease, tokens", "int", ""), ("sync_age_ms", "int", "")],
         kind="ext", caption="every 429, 1 % of allows; 30 days")
e.entity("lb", 30, 460, 470, "local bucket  (memory)", [("key", "customer:endpoint", "PK"), ("tokens", "float", ""), ("refilled_at", "monotonic", ""),
         ("lease, lease_until", "int, ts", "")], kind="redis", caption="one per active key, per server")
e.entity("gb", 570, 460, 470, "global bucket  (quota svc)", [("key", "customer:endpoint", "PK"), ("tokens", "float", ""), ("asked", "per server", ""),
         ("policy_v", "int", "")], kind="redis", caption="memory, mirrored to a standby")
e.entity("xb", 1110, 460, 460, "exact bucket  (Redis hash)", [("rl:{customer}:endpoint", "key", "PK"), ("tokens", "float", ""), ("ts", "ms", "")],
         kind="redis", caption="exact-mode keys only; TTL 2 × refill")
e.rel("po", "ti", "N", "1", src="l:0.35", dst="r:0.35", label="")
e.save(OUT / "erd-physical.svg", order=["ti", "po", "lb", "gb", "xb", "de"])

# ── the lifecycle of one policy version (chapter 3, challenge 5) ──
m = States(1640, 600, box=(330, 140), size=31)
m.state("draft", 40, 60, "Draft", "validated")
m.start("draft")
m.state("shadow", 460, 60, "Shadow", "logged, not enforced")
m.go("draft", "shadow", "approve")
m.state("canary", 880, 60, "Canary", "1 % of servers, 5 min", kind="warn")
m.go("shadow", "canary", "looks right")
m.state("enf", 1290, 60, "Enforced", "every server", kind="final")
m.go("canary", "enf", "429s steady")
m.state("rb", 880, 400, "Rolled back", "previous version", kind="bad")
m.go("canary", "rb", "429s double")
m.go("enf", "rb", "one command")
m.state("sup", 1290, 400, "Superseded", "kept 3 versions")
m.go("enf", "sup", "next version")
m.save(OUT / "state-policy.svg")


# ── figures ──
def tension():
    """One customer, three answers to 'how does each server know?'."""
    p = [T(40, 50, "1,000 requests a minute, 500 servers: three ways for each server to know", 28, INK, 800)]
    stages = [("Exact", "One central counter", "+1.2 ms at p99", "every request waits on the store; when it is down, so is the API", RED, "#fce8e6"),
              ("Split", "The limit ÷ 500", "2 per server per minute", "traffic on 3 servers: throttled at 0.6 % of the quota", AMBER, "#fef7e0"),
              ("Leased", "Leases that follow demand", "≤ 5 % over · 2 µs", "decided in memory; survives its own dependencies", GREEN, "#e6f4ea")]
    for i, (t, name, n, note, col, fill) in enumerate(stages):
        x = 60 + i * 510
        p += [R(x, 100, 470, 270, fill, col, rx=14), T(x + 24, 150, t, 30, col, 800), T(x + 24, 196, name, 26, INK, 800),
              T(x + 24, 250, n, 32, INK, 800)]
        words, line, ys = note.split(), "", 296
        for w_ in words:
            if len(line) + len(w_) > 36: p.append(T(x + 24, ys, line, 22, INK, 500)); line, ys = w_, ys + 30
            else: line = (line + " " + w_).strip()
        p.append(T(x + 24, ys, line, 22, INK, 500))
    p += [L(60, 420, 1540, 420, BLUE, 4), T(60, 462, "← exact, slow, a dependency", 24, RED, 800),
          T(1540, 462, "bounded, fast, never the outage →", 24, GREEN, 800, "end")]
    (OUT / "tension.svg").write_text(svgdoc(1600, 490, "".join(p)))


def boundary():
    """The fixed window's boundary burst against a token bucket, on the same two seconds."""
    p = [T(40, 48, "The same 2,000 requests, 11:59:59 and 12:00:00, limit 1,000 a minute", 28, INK, 800)]
    rows = [("Fixed window, per minute", [("11:59:59", 1000, 0, "1,000 admitted: window 11:59 empty"), ("12:00:00", 1000, 0, "1,000 admitted: a new window")],
             "2,000 in one second", RED),
            ("Token bucket, 16.7/s, burst 200", [("11:59:59", 200, 800, "200 admitted, 800 get 429"), ("12:00:00", 17, 983, "17 admitted: one second of refill")],
             "217: at most b + r × t", GREEN)]
    y = 100
    for title, bars, verdict, col in rows:
        p.append(T(60, y + 34, title, 26, INK, 800))
        p.append(T(1540, y + 34, verdict, 26, col, 800, "end"))
        by = y + 60
        for j, (t, ok, rej, note) in enumerate(bars):
            yy = by + j * 70
            p.append(T(60, yy + 38, t, 24, GREY, 700))
            sc = 0.9
            p.append(R(200, yy + 8, max(ok * sc, 6), 44, "#e8f0fe" if col == GREEN else "#fce8e6", BLUE if col == GREEN else RED, rx=6))
            if rej: p.append(R(200 + ok * sc, yy + 8, rej * sc, 44, "#f1f3f4", GREY, rx=6, sw=1.6))
            p.append(T(1130, yy + 38, note, 23, INK, 600))
        y += 230
    (OUT / "boundary.svg").write_text(svgdoc(1600, 580, "".join(p)))


tension()
boundary()
budget_bar(OUT / "budget.svg", [("lookup + script", 0.1, "service"), ("Redis round trip at p99", 1.2, "data")],
           total=1, unit="ms", title="The exact path: one script per request, against a 1 ms p99 budget (illustrative)")
print(sorted(p.name for p in OUT.glob("*.svg")))
