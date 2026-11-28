"""SD-03: the pictures that are not C4 views -> ./svg/ (sequences, the physical data model, the hour's lifecycle, figures).
Every C4 view (context, containers, V1 -> V3, flows, challenge zooms, recap, alternate) comes from ../workspace.dsl +
../views.json through c4-structurizr; this file never draws a box of the architecture.
Run by ref_solution.py diagrams (which renders the C4 views first, into the same folder); never clears svg/."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]                     # the repo
sys.path.insert(0, str(ROOT / ".claude/skills/reference-solution/kit"))
import seqsvg as sq                                                     # noqa: E402
import erdsvg as er                                                     # noqa: E402
from statesvg import States                                             # noqa: E402
from figsvg import budget_bar, svgdoc, T, R, L, esc                    # noqa: E402
from gtheme import ink                                                  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
FONT = "Inter, Roboto, sans-serif"
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

seq("seq-ingest",
    [("sdk", "Ad SDK", "person"), ("col", "Collector", "container"), ("kf", "Kafka: events.raw", "queue")],
    [("m", "sdk", "col", "POST /v1/events: 500 events, IDs minted at creation"),
     ("n", "col", "col", "validate; stamp server time; clamp a skewed client time", "amber"),
     ("m", "col", "kf", "produce, key = event ID, acks=all"),
     ("r", "kf", "col", "ack: 2 of 3 replicas have it"),
     ("r", "col", "sdk", "202 accepted: 500", dict(hl=True)),
     ("n", "sdk", "sdk", "no answer? retry the same batch: same IDs", "amber")])

seq("seq-retry",
    [("sdk", "Ad SDK", "person"), ("col", "Collector", "container"), ("kf", "Kafka partition 311", "queue"), ("fl", "Deduplicator", "container")],
    [("m", "sdk", "col", "batch B17 (click e7f3…)"),
     ("m", "col", "kf", "append: offset 81,220"),
     ("r", "kf", "col", "ack"),
     ("n", "col", "sdk", "202 lost on the cell network", "amber"),
     ("m", "sdk", "col", "retry B17: the same IDs"),
     ("m", "col", "kf", "append: offset 81,977 (same key, same partition)"),
     ("m", "kf", "fl", "both records", dict(kind="async")),
     ("n", "fl", "fl", "e7f3 is in state since 81,220: drop the second", "green"),
     ("n", "fl", "fl", "billing job: first row per event ID in hour 10:00", "green")])

seq("seq-watermark",
    [("p1", "Partition 1", "queue"), ("p2", "Partition 2", "queue"), ("w", "Window: ad 77, 14:00", "container"), ("ch", "Live store", "db")],
    [("m", "p1", "w", "impression, event time 14:00:58", dict(kind="async")),
     ("m", "p2", "w", "impression, event time 14:01:30", dict(kind="async")),
     ("n", "w", "w", "watermark = min over partitions of (latest − 2 min) = 13:58:58", "blue"),
     ("m", "w", "ch", "early result: 1,212, version 1"),
     ("m", "p1", "w", "impression, event time 14:03:05", dict(kind="async")),
     ("m", "p2", "w", "impression, event time 14:03:40", dict(kind="async")),
     ("n", "w", "w", "watermark 14:01:05 passes 14:01: the minute is complete", "green"),
     ("m", "w", "ch", "on time: 1,318, version 2 replaces version 1", dict(hl=True)),
     ("m", "p1", "w", "late: event time 14:00:40, within the hour", dict(kind="async")),
     ("m", "w", "ch", "update: 1,319, version 3")], size=26, row=46, width=1760)

seq("seq-replay",
    [("op", "On-call", "person"), ("fl", "Flink, new build", "container"), ("ch", "ClickHouse", "db"), ("job", "Billing job", "container"), ("bt", "Billing tables", "db")],
    [("m", "op", "fl", "redeploy; rewind offsets to 10:00"),
     ("m", "fl", "ch", "minutes 10:00 – 14:00 again, higher versions"),
     ("n", "ch", "ch", "same key, higher version: replaces, does not add", "green"),
     ("m", "op", "job", "re-run hour 10:00 with its manifest"),
     ("m", "job", "bt", "identical rows: the commit changes nothing", dict(hl=True))])

seq("seq-correct",
    [("fr", "Fraud system", "ext"), ("iv", "Invalidations", "queue"), ("cl", "Hour closer", "container"), ("job", "Billing job", "container"), ("inv", "Invoicing", "ext")],
    [("m", "fr", "iv", "invalidate 3.1 M clicks: botnet 17, with their hours"),
     ("m", "iv", "cl", "hours from 4 Oct 13:00 marked dirty", dict(kind="async")),
     ("m", "cl", "job", "re-run each dirty hour, new manifest"),
     ("n", "job", "job", "write version 2 of each hour; v1 stays", "green"),
     ("n", "job", "job", "version 2 − invoiced version 1 = −$1.55 M", "amber"),
     ("m", "job", "inv", "adjustment lines on the next invoice", dict(hl=True))])

# ── the physical data model ──
e = er.ERD(1600, 820, size=25)
e.entity("ev", 30, 40, 470, "events  (Iceberg)", [("event_id", "uuid", "PK"), ("type", "imp | click", ""), ("impression_id", "uuid", "IX"),
         ("ad_id", "bigint", ""), ("event_time", "ts", ""), ("server_ts", "ts", ""), ("clamped", "bool", "")],
         kind="focus", caption="partitioned by event hour; 0.6 PB a month")
e.entity("bh", 570, 40, 470, "billing_hour  (Iceberg)", [("campaign_id", "bigint", "PK"), ("ad_id", "bigint", "PK"), ("hour", "ts", "PK"),
         ("version", "int", "PK"), ("clicks", "bigint", ""), ("cost_micros", "bigint", ""), ("manifest_id", "uuid", "FK")],
         caption="a correction adds a version; none is edited")
e.entity("mf", 1110, 40, 460, "manifest", [("manifest_id", "uuid", "PK"), ("events_snapshot", "bigint", ""), ("rate_card_v", "int", ""),
         ("invalid_snapshot", "bigint", ""), ("image_digest", "text", "")], kind="ext", caption="what one run read")
e.entity("lm", 30, 470, 470, "live_minute  (ClickHouse)", [("campaign_id, ad_id", "bigint", "PK"), ("minute", "ts", "PK"), ("shard", "uint8", "PK"),
         ("impressions, clicks", "uint64", ""), ("version", "uint64", "")], kind="redis", caption="ReplacingMergeTree by version")
e.entity("iv", 570, 470, 470, "invalidation", [("event_id", "uuid", "PK"), ("hour", "ts", "IX"), ("reason", "text", ""), ("detected_at", "ts", "")],
         caption="append-only")
e.entity("aj", 1110, 470, 460, "adjustment", [("campaign_id", "bigint", "PK"), ("hour", "ts", "PK"), ("to_version", "int", "PK"), ("delta_micros", "bigint", "")],
         caption="what invoicing applies")
e.rel("bh", "mf", "N", "1", src="r:0.8", dst="l:0.5", label="")
e.rel("iv", "ev", "N", "1", src="l:0.25", dst="b:0.87", via=[(439, 530)], label="")
e.rel("aj", "bh", "N", "1", src="t:0.3", dst="b:0.6", label="")
e.save(OUT / "erd-physical.svg", order=["ev", "bh", "mf", "lm", "iv", "aj"])


# ── the lifecycle of one billing hour (challenges 2 and 5) ──
m = States(1640, 600, box=(340, 150), size=32)
m.state("open", 70, 70, "Open", "provisional")
m.start("open")
m.state("v1", 650, 70, "Final v1", "invoiced", kind="final")
m.go("open", "v1", "at H + 48 h")
m.state("dirty", 1230, 70, "Dirty", "re-run pending", kind="warn")
m.go("v1", "dirty", "fraud flags")
m.state("vn", 940, 410, "Final v+1", "adjustment sent", kind="final")
m.go("dirty", "vn", "re-run")
m.go("vn", "dirty", "flags again", bend=150)
m.save(OUT / "state-hour.svg")

# ── figures ──
def tension():
    """One hour's number, three times: fast and provisional, exact and final, corrected."""
    p = [T(40, 50, "One hour's number, three times: each later one is slower, more exact, and the one that counts", 28, INK, 800)]
    stages = [("+10 s", "Live", "1,319,402", "provisional: duplicates within 10 min removed; late events still coming", BLUE, "#e8f0fe"),
              ("+48 h", "Final, version 1", "1,318,977", "exact: every duplicate removed, late events in; invoiced", GREEN, "#e6f4ea"),
              ("+9 days", "Version 2", "1,291,045", "fraud invalidated 2 %: an adjustment line, never an edit", AMBER, "#fef7e0")]
    for i, (t, name, n, note, col, fill) in enumerate(stages):
        x = 60 + i * 510
        p += [R(x, 110, 470, 250, fill, col, rx=14), T(x + 24, 160, t, 30, col, 800), T(x + 24, 205, name, 26, INK, 800),
              T(x + 24, 258, n, 34, INK, 800)]
        words, line, ys = note.split(), "", 300
        for w_ in words:
            if len(line) + len(w_) > 36: p.append(T(x + 24, ys, line, 21, INK, 500)); line, ys = w_, ys + 28
            else: line = (line + " " + w_).strip()
        p.append(T(x + 24, ys, line, 21, INK, 500))
        if i < 2: p.append(f'<path d="M{x+480},235 l22,0" stroke="{GREY}" stroke-width="3" marker-end="url(#ar)"/>')
    p.insert(0, f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,1 L10,5 L0,9 z" fill="{GREY}"/></marker></defs>')
    p += [L(60, 420, 1540, 420, BLUE, 4), T(60, 462, "← faster, cheaper, provisional", 24, BLUE, 800),
          T(1540, 462, "exact, auditable, billed →", 24, GREEN, 800, "end")]
    (OUT / "tension.svg").write_text(svgdoc(1600, 490, "".join(p)))

tension()
budget_bar(OUT / "budget.svg", [("SDK batching", 1.0, "client"), ("collector + log", 0.5, "edge"), ("early firing", 2.0, "service"),
                                ("store insert", 1.0, "data"), ("query", 1.0, "cache")],
           total=10, unit="s", title="From an impression to the dashboard, worst case (initial target p99 10 s)")
print(sorted(p.name for p in OUT.glob("*.svg")))
