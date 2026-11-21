#!/usr/bin/env python3
"""SD-94 distributed denylist: every picture for the video and the written design -> ./svg/*.svg.
One carried baseline (declared once), numbered flows, challenge overlays, C4, sequences, ERDs, figures.
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
b = bs.Baseline(1600, 740)
b.node("policy", 20, 300, 180, 130, "client", "Policy tool", "operators · feeds")
b.node("rules", 350, 300, 180, 130, "data", "Rule store", "one version order", since=2, shape="db")
b.node("origin", 680, 300, 180, 130, "data", "Origin store", "versions", shape="db")
b.node("relay", 1010, 300, 180, 130, "edge", "Relay tree", "regional · zone", since=2, stack=True)
b.node("node", 1360, 300, 220, 130, "service", "Enforcement node", "local set · atomic swap")
b.node("req", 1360, 90, 220, 100, "client", "Requests", "source address")
b.node("ctrl", 680, 500, 180, 100, "service", "Controller", "gates · state", since=3)
# tags: shown only inside a challenge, a flow or the recap. Every tag has its own slot, so all can show at once.
b.node("manifest", 1010, 590, 180, 100, "data", "Manifest", "window · kill flag", tag="ch1")
b.node("val", 350, 590, 180, 100, "service", "Validate", "allowlist · limits", tag="ch3")
b.node("lkg", 1360, 590, 220, 100, "data", "Last good", "on disk", shape="db", tag="ch4")
b.node("lb", 680, 90, 180, 110, "edge", "Load balancer", "drains stale", tag="ch4")
b.node("lookup", 1010, 90, 180, 100, "data", "Lookup", "exact tier", stack=True, tag="ch5")
b.node("auth", 20, 90, 180, 100, "ext", "Authority", "slow API", tag="ch6")
b.node("adapter", 350, 90, 180, 100, "service", "Mirror", "cache · budget", tag="ch6")
b.node("metrics", 680, 650, 180, 80, "ext", "Metrics", "probes", tag="ch7")

REQ = dict(src="r:0.25", dst="l:0.25")
b.edge("p-o", "policy", "origin", "write list file", until=1, **REQ)
b.edge("o-n", "origin", "node", "download all", until=1, **REQ, at=(1010, 340))
b.edge("p-r", "policy", "rules", "publish", since=2, **REQ)
b.edge("r-o", "rules", "origin", "snapshots", since=2, **REQ)
b.edge("o-rel", "origin", "relay", "fan-out", since=2, **REQ)
b.edge("poll", "node", "relay", "poll", src="l:0.25", dst="r:0.25", since=2, at=(1275, 322))
b.edge("push", "relay", "node", "push", src="r:0.5", dst="l:0.5", since=2, kind="async", at=(1275, 362))
b.edge("delta", "relay", "node", "delta", src="r:0.8", dst="l:0.8", since=2, kind="resp", at=(1275, 408))
b.edge("rq", "req", "node", "check", src="b:0.45", dst="t:0.45", at=(1495, 235))
b.edge("rs", "node", "req", "verdict", src="t:0.9", dst="b:0.9", kind="resp", at=(1522, 272))
b.edge("n-c", "node", "ctrl", "applied version", src="b:0.12", dst="r:0.3", via=[(1386, 530)], since=3, kind="async", at=(1280, 518))
b.edge("c-o", "ctrl", "origin", "stage", src="t:0.5", dst="b:0.5", since=3, at=(742, 470))
b.edge("p-c", "policy", "ctrl", "halt · rollback", src="b:0.3", dst="b:0.5", via=[(75, 722), (770, 722)], tag="ops", at=(420, 708))
b.edge("rel-m", "relay", "manifest", "manifest", src="b:0.2", dst="t:0.2", tag="ch1", at=(1090, 520))
b.edge("v-r", "val", "rules", "check", src="t:0.5", dst="b:0.5", tag="ch3", at=(470, 515))
b.edge("n-l", "node", "lkg", "persist", src="b:0.7", dst="t:0.7", tag="ch4", at=(1555, 520))
b.edge("n-lb", "node", "lb", "age", src="t:0.08", dst="b:0.5", via=[(1378, 255), (770, 255)], tag="ch4", kind="async", at=(1100, 243))
b.edge("n-lk", "node", "lookup", "maybe", src="t:0.22", dst="b:0.5", via=[(1408, 225), (1100, 225)], tag="ch5", at=(1250, 213))
b.edge("a-ad", "auth", "adapter", "feed", src="r:0.5", dst="l:0.5", tag="ch6", at=(275, 130))
b.edge("ad-r", "adapter", "rules", "mirror", src="b:0.5", dst="t:0.5", tag="ch6", at=(440, 250))
b.edge("c-m", "ctrl", "metrics", "SLIs", src="b:0.5", dst="t:0.5", tag="ch7", at=(742, 626))

def sv(name, h, **view):
    b.h = h
    b.save(OUT / name, **view)
sv("base-v1.svg", 470, upto=1, legend=True)
sv("base-v2.svg", 470, upto=2, new=2, legend=True)
sv("base-v3.svg", 700, upto=3, new=3, legend=True)
ALL = ["ch1", "ch3", "ch4", "ch5", "ch6", "ch7"]
sv("base-final.svg", 790, upto=3, show=ALL, legend=True)
sv("map.svg", 790, upto=3, show=ALL, legend=True, attack=["node", "relay", "rules", "origin"], keep=None)
sv("flow-fr1.svg", 700, upto=3, show=["ch3"], flow=["p-r", "r-o", "v-r"],
   notes=[(560, 480, 700, "Normalise, validate, approve, then one transaction assigns the next version.", "blue")])
sv("flow-fr2.svg", 640, upto=3, flow=["o-rel", "push", "poll", "delta"],
   notes=[(40, 480, 760, "A poll asks the manifest only. Deltas when behind inside the window; a snapshot only to bootstrap.", "blue")])
sv("flow-fr3.svg", 470, upto=3, flow=["rq", "rs"],
   notes=[(560, 160, 700, "Allowlist first, then exact, then longest prefix. The verdict carries the rule version. No network call.", "blue")])
sv("flow-fr4.svg", 740, upto=3, show=["ch7"], flow=["n-c", "c-m"],
   notes=[(40, 440, 560, "Each node reports version and age; decisions are sampled with their version.", "blue")])
sv("flow-fr5.svg", 740, upto=3, show=["ops", "ch1"], flow=["p-c", "c-o"],
   notes=[(900, 440, 600, "Halt the stage, flip the kill flag, or publish the old content as a higher version.", "blue")])
sv("ch1-attack.svg", 570, upto=3, attack=["node"], keep=["relay", "node", "origin"], hot=["delta", "poll"],
   notes=[(500, 470, 760, "Offline two hours. Nothing says what to fetch, or whether what arrived is whole.", "red")])
sv("ch1-fix.svg", 700, upto=3, show=["ch1"], fix=["manifest"], keep=["relay", "node", "manifest"], ok=["rel-m", "poll", "delta"],
   notes=[(500, 470, 760, "Manifest: have=V. Inside the window: deltas. Outside: one snapshot. Verify, then swap.", "green")])
sv("ch2-attack.svg", 570, upto=3, attack=["node"], keep=["relay", "node"], hot=["push", "delta"],
   notes=[(500, 470, 760, "The node applies in arrival order: 101 then 100 leaves the key banned.", "red")])
sv("ch2-fix.svg", 570, upto=3, fix=["node"], keep=["relay", "node"], ok=["push", "delta"],
   notes=[(500, 470, 760, "Apply a change only if its version is higher than the key's last. Replays are no-ops.", "green")])
sv("ch3-attack.svg", 570, upto=3, attack=["relay"], keep=["policy", "rules", "origin", "relay", "node"], hot=["r-o", "o-rel", "delta"],
   notes=[(560, 470, 760, "A typo reaches every node in about 18 seconds. Nothing asks if the content is plausible.", "red")])
sv("ch3-fix.svg", 740, upto=3, show=["ch3", "ch1"], fix=["val", "ctrl", "manifest"], keep=["rules", "origin", "relay", "node", "val", "manifest", "ctrl"], ok=["v-r", "c-o", "rel-m"],
   notes=[(900, 440, 640, "Validate, allowlist, staged rollout gated on block rate, kill flag on its own channel.", "green")])
sv("ch4-attack.svg", 570, upto=3, attack=["node"], keep=["relay", "node", "req"], hot=["poll", "push"],
   notes=[(500, 470, 760, "Three hours with no updates. Fail closed refuses everything; fail open serves banned sources.", "red")])
sv("ch4-fix.svg", 700, upto=3, show=["ch4"], fix=["lkg", "lb"], keep=["relay", "node", "lkg", "lb", "req"], ok=["n-l", "n-lb"],
   notes=[(500, 470, 760, "Stale is not open: keep enforcing. Past the bound, drain the node, capped.", "green")])
sv("ch5-attack.svg", 570, upto=3, attack=["node"], keep=["node", "req"], hot=["rq"],
   notes=[(500, 470, 760, "100 million IPv6 prefixes: 1.7 GB exact. The filter alone blocks real users.", "red")])
sv("ch5-fix.svg", 570, upto=3, show=["ch5"], fix=["lookup", "node"], keep=["node", "lookup", "req"], ok=["n-lk"],
   notes=[(560, 470, 760, "Filter says 'not listed' locally. A 'maybe' is confirmed by an exact tier, then cached.", "green")])
sv("ch6-attack.svg", 570, upto=3, show=["ch6"], attack=["adapter", "auth"], keep=["rules", "adapter", "auth"], hot=["a-ad"],
   notes=[(560, 470, 760, "20,000 new addresses a second against a 100 call a second budget.", "red")])
sv("ch6-fix.svg", 570, upto=3, show=["ch6"], fix=["adapter"], keep=["rules", "adapter", "auth", "origin"], ok=["a-ad", "ad-r"],
   notes=[(560, 470, 760, "Mirror a bulk list if one exists; otherwise a bounded verdict cache, a budget and a stated policy.", "green")])
sv("ch7-attack.svg", 570, upto=3, attack=["relay"], keep=["relay", "node", "ctrl"],
   notes=[(500, 470, 760, "The relay dashboard is green. One region is a version behind.", "red")])
sv("ch7-fix.svg", 740, upto=3, show=["ch7"], fix=["metrics"], keep=["ctrl", "metrics", "node", "relay"], ok=["c-m", "n-c"],
   notes=[(900, 440, 640, "Measure the promise: version skew, probes, block-rate anomaly, a decision log with versions.", "green")])
bs.budget_bar(OUT / "budget.svg", [("compile", 3, "service"), ("origin → regional", 2, "edge"), ("regional → zone", 2, "edge"),
                                   ("poll wait, up to", 10, "queue"), ("verify + apply", 1, "data")],
              total=30, unit="s", title="A ban lands on a node, pull-only worst case (initial target 30 s)")

# ───────────────────────────── 2 · C4 ────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.node("pol", 60, 90, 300, 150, "person", "Policy owner", "Person", "Security and legal decide what is listed.")
d.node("sre", 60, 520, 300, 150, "person", "Platform operator", "Person", "Runs the pipeline, halts a push.")
d.node("dl", 620, 290, 360, 200, "system", "Denylist system", "Software System", "Versioned lists, distribution, local check.")
d.node("auth", 1230, 90, 320, 150, "ext", "External authority", "External system", "Publishes a bulk list or a lookup API.")
d.node("fleet", 1230, 520, 320, 150, "ext", "Serving fleet", "External systems", "100,000 nodes that serve user requests.")
d.edge("pol", "dl", "Publish changes", "console, API", src="r:0.8", dst="l:0.25", at=(480, 255))
d.edge("auth", "dl", "Bulk list or verdicts", "file, HTTPS", src="l:0.5", dst="t:0.7", at=(1120, 170))
d.edge("sre", "dl", "Rollout, halt, rollback", "audited API", src="r:0.2", dst="l:0.8", at=(480, 560))
d.edge("dl", "fleet", "Versions, manifests", "HTTPS pull + push", src="r:0.7", dst="l:0.3", at=(1110, 440))
d.legend(40, 780, ("person", "system", "ext"))
d.save(OUT / "c4-context.svg")

d = c4.Diagram(1600, 900)
d.boundary(30, 60, 1130, 780, "Denylist system", "Software System")
d.node("tool", 60, 330, 220, 160, "container", "Policy tool", "Web app + API", "Publish, approve, explain.", size=21)
d.node("ing", 330, 330, 220, 160, "container", "Ingest + rule store", "Service + database", "Normalise, validate, one version order.", size=21)
d.node("cmp", 600, 330, 220, 160, "container", "Compiler + origin", "Job + object storage", "Snapshots, deltas, manifests.", size=21)
d.node("rel", 870, 330, 250, 160, "container", "Relay tree", "Caching services", "Regional, then zone. Push and poll.", size=21, stack=True)
d.node("ctl", 600, 640, 220, 140, "container", "Control plane", "Service", "Rollout, gates, fleet state.", size=21)
d.node("node", 1260, 330, 280, 160, "container", "Enforcement agent", "Library in the server", "Local set, atomic swap, verdict.", size=21)
d.node("srv", 1260, 90, 280, 130, "ext", "Serving process", "External", "Calls Check on each request.")
d.node("auth", 330, 90, 220, 130, "ext", "External authority", "External", "Bulk list or lookup.")
d.edge("tool", "ing", "PublishChange", "HTTPS", src="r", dst="l", at=(440, 310))
d.edge("ing", "cmp", "new version", "SQL, files", src="r", dst="l", at=(710, 310))
d.edge("cmp", "rel", "artifacts", "object API", src="r", dst="l", at=(985, 310))
d.edge("rel", "node", "poll, push, delta", "HTTPS", src="r", dst="l", at=(1190, 310))
d.edge("srv", "node", "Check(key)", "in process", src="b", dst="t", at=(1400, 280))
d.edge("ctl", "cmp", "stage, halt", "", src="t", dst="b", at=(710, 575))
d.edge("auth", "ing", "mirror", "file", src="b", dst="t", at=(520, 255))
d.legend(40, 860, ("person", "container", "db", "ext"))
d.save(OUT / "c4-containers.svg")

# ───────────────────────────── 3 · sequences ─────────────────────────────────────────────────────────
def seq(name, parts, steps, **kw):
    s = sq.Seq(1500, size=22, row=50, **kw)
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
    [("op", "Operator", "person"), ("ing", "Ingest", "container"), ("rs", "Rule store", "db"), ("cp", "Compiler", "container")],
    [("m", "op", "ing", "PublishChange(ops, idempotencyKey)"),
     ("n", "ing", "ing", "normalise CIDR and v6; size limit; allowlist check; approval if large"),
     ("m", "ing", "rs", "one transaction: write rules, take the next version N"),
     ("r", "rs", "ing", "version N, audit event written"),
     ("m", "rs", "cp", "version N exists", dict(kind="async")),
     ("n", "cp", "cp", "build snapshot N and delta N-1 to N; checksum chained to N-1", "green"),
     ("r", "ing", "op", "accepted, version N, rollout stage 0")])

seq("seq-distribute",
    [("rel", "Zone relay", "container"), ("nd", "Node", "container"), ("dk", "Disk", "db")],
    [("m", "rel", "nd", "push: version N exists", dict(kind="async")),
     ("m", "nd", "rel", "manifest(have = N-1)"),
     ("r", "rel", "nd", "inside the window: delta N-1 to N, checksum"),
     ("n", "nd", "nd", "verify the checksum chain; build the new structure beside the old", "green"),
     ("n", "nd", "nd", "swap one pointer: old list until this instant, new list after", "green"),
     ("m", "nd", "dk", "write snapshot and version file (last known good)"),
     ("m", "nd", "rel", "applied N, age 0 (with the next poll)", dict(kind="async"))])

seq("seq-enforce",
    [("rq", "Request", "person"), ("ag", "Agent", "container"), ("lg", "Decision log", "db")],
    [("m", "rq", "ag", "Check(203.0.113.9)"),
     ("n", "ag", "ag", "normalise; allowlist first: not allowlisted"),
     ("n", "ag", "ag", "exact lookup, then longest-prefix range lookup"),
     ("r", "ag", "rq", "deny, rule 4411, version 8,361,004", dict(hl=True)),
     ("m", "ag", "lg", "sample: key, verdict, rule, version (off the hot path)", dict(kind="async"))])

seq("seq-rollback",
    [("op", "Operator", "person"), ("cp", "Control plane", "container"), ("og", "Origin", "db"), ("nd", "Nodes", "container")],
    [("n", "cp", "cp", "gate: block rate on the canary is 8 points over baseline", "red"),
     ("m", "cp", "og", "halt version N: later stages do not receive it", dict(hl=True)),
     ("m", "op", "cp", "Rollback(to M)"),
     ("m", "cp", "og", "publish M's content as version N+1 (higher, never reused)"),
     ("m", "og", "nd", "N+1 distributed by the normal path", dict(kind="async")),
     ("n", "nd", "nd", "canary nodes apply N+1: block rate returns to baseline", "green")])

seq("seq-ch1-catchup",
    [("nd", "Node z7-0412", "container"), ("rel", "Zone relay", "container"), ("org", "Origin", "db")],
    [("n", "nd", "nd", "offline 2 hours; last applied 8,000,000", "red"),
     ("m", "nd", "rel", "manifest(have = 8,000,000)"),
     ("r", "rel", "nd", "current 8,360,000; inside the window: deltas, ~11 MB"),
     ("n", "nd", "nd", "checksum does not match on the last delta: discard", "red"),
     ("m", "nd", "rel", "manifest(snapshot) after a failed apply"),
     ("m", "rel", "org", "snapshot 8,360,000 (cached for the zone)", dict(kind="async")),
     ("r", "rel", "nd", "snapshot, 40 MB, checksum"),
     ("n", "nd", "nd", "verify, build beside, swap, report applied 8,360,000", "green")])

seq("seq-ch2-merge",
    [("sr", "Source", "container"), ("nd", "Node", "container")],
    [("m", "sr", "nd", "v101: remove 203.0.113.9  (arrives first)"),
     ("n", "nd", "nd", "key 203.0.113.9: last version 0 → set removed at 101", "green"),
     ("m", "sr", "nd", "v100: add 203.0.113.9  (arrives late)", dict(hl=True)),
     ("n", "nd", "nd", "100 is not higher than 101: ignore. Final state: removed", "green"),
     ("m", "sr", "nd", "v101 again (duplicate)"),
     ("n", "nd", "nd", "101 is not higher than 101: no-op", "green")])

seq("seq-ch4-drain",
    [("nd", "Node eu-3-0099", "container"), ("lb", "Load balancer", "container"), ("cp", "Control plane", "container")],
    [("n", "nd", "nd", "no update for 15 min: past the bound for the abuse list", "red"),
     ("m", "nd", "lb", "health: stale, age 15 min", dict(kind="async")),
     ("n", "lb", "lb", "drain budget: 5 % per region not yet used", "amber"),
     ("m", "lb", "nd", "out of rotation; keeps enforcing its last list", dict(hl=True)),
     ("m", "nd", "cp", "poll succeeds; applies the delta", dict(kind="async")),
     ("m", "nd", "lb", "health: current, age 2 s"),
     ("n", "lb", "lb", "back in rotation", "green")])

seq("seq-ch5-lookup",
    [("rq", "Request", "person"), ("ag", "Agent", "container"), ("lk", "Lookup tier", "db")],
    [("m", "rq", "ag", "Check(2001:db8:77::5)"),
     ("n", "ag", "ag", "local filter: maybe listed"),
     ("m", "ag", "lk", "exact lookup (coalesced with equal requests)"),
     ("r", "lk", "ag", "not listed (a false positive): allow, cache 60 s"),
     ("r", "ag", "rq", "allow"),
     ("n", "ag", "ag", "per-node lookup budget protects the tier during an attack", "amber")])

seq("seq-ch6-authority",
    [("ag", "Agent", "container"), ("ad", "Mirror + cache", "container"), ("au", "Authority", "ext")],
    [("m", "ag", "ad", "verdict(192.0.2.7)"),
     ("n", "ad", "ad", "range cache: no entry; budget has tokens; single flight"),
     ("m", "ad", "au", "lookup(192.0.2.7)"),
     ("r", "au", "ad", "banned, covers 192.0.0.0/16, valid 24 h"),
     ("n", "ad", "ad", "store the range rule with a version; supersedes per-address verdicts", "green"),
     ("r", "ad", "ag", "deny"),
     ("n", "ad", "ad", "API down: serve expired entries within the grace period, flag the decisions", "amber")])

seq("seq-ch7-probe",
    [("pb", "Probe", "container"), ("cp", "Control plane", "container"), ("nd", "Node in each region", "container")],
    [("m", "pb", "cp", "publish a synthetic banned key as version N (every 5 min)"),
     ("n", "cp", "nd", "normal distribution carries it", "amber"),
     ("m", "pb", "nd", "send a request from the synthetic key through the real path"),
     ("r", "nd", "pb", "deny within 30 s: probe passes", dict(hl=False)),
     ("n", "pb", "pb", "region ap-2 still allows after 30 s: page, with the node's applied version", "red")])

# ───────────────────────────── 4 · data models ───────────────────────────────────────────────────────
c = er.Chen(1600, 900, size=26)
c.entity("l", 200, 120, "LIST"); c.entity("r", 680, 120, "RULE"); c.entity("v", 1200, 120, "VERSION")
c.entity("n", 1200, 560, "NODE"); c.entity("a", 200, 560, "AUDIT EVENT", weak=True); c.entity("w", 680, 700, "ALLOW RANGE")
c.rel("co", 440, 120, "CONTAINS"); c.rel("pb", 940, 120, "PUBLISHED IN"); c.rel("ap", 1200, 340, "APPLIES")
c.rel("lg", 200, 340, "LOGGED AS", identifying=True); c.rel("pr", 680, 400, "PROTECTS")
c.attr("lid", 200, 40, "list_id", of="l", key=True); c.attr("cl", 80, 190, "class", of="l")
c.attr("k", 600, 40, "key", of="r", key=True); c.attr("ac", 780, 40, "action", of="r"); c.attr("ex", 860, 200, "expires_at", of="r")
c.attr("n#", 1200, 40, "version_n", of="v", key=True); c.attr("ck", 1400, 120, "checksum", of="v", derived=True)
c.attr("nid", 1200, 650, "node_id", of="n", key=True); c.attr("ver", 1400, 460, "applied", of="n", derived=True)
c.attr("rs", 200, 650, "reason", of="a", partial=True)
c.link("l", "co", "1"); c.link("co", "r", "N", total=True)
c.link("r", "pb", "N"); c.link("pb", "v", "1")
c.link("n", "ap", "N", src="t", dst="b"); c.link("ap", "v", "1", src="t", dst="b")
c.link("l", "lg", "1", src="b", dst="t"); c.link("lg", "a", "N")
c.link("w", "pr", "N", src="t", dst="b"); c.link("pr", "r", "1", src="t", dst="b")
c.legend(1380, 690)
c.note(380, 800, 700, "A key has at most one live state per list; the version of its last change decides it.")
c.save(OUT / "erd-chen.svg")

e = er.ERD(1600, 800, size=22)
e.entity("rule", 30, 40, 520, "rule", [("list_id", "text", "PK,FK"), ("key_bytes", "bytea", "PK"), ("kind", "text", ""), ("action", "text", ""),
         ("added_version", "bigint", "IX"), ("removed_version", "bigint", ""), ("reason", "text", ""), ("expires_at", "ts", "")],
         kind="focus", caption="10 M rows; a removed key stays for the delta window")
e.entity("ver", 690, 40, 420, "version", [("list_id", "text", "PK,FK"), ("n", "bigint", "PK"), ("checksum", "bytea", ""),
         ("prev_checksum", "bytea", ""), ("snapshot_ref", "text", ""), ("delta_ref", "text", ""), ("stage", "text", "")],
         caption="n is assigned in the same transaction as the rules")
e.entity("ns", 1250, 40, 330, "node_state", [("node_id", "text", "PK"), ("list_id", "text", "PK"), ("version", "bigint", ""), ("applied_at", "ts", "")],
         kind="ext", caption="soft state, rebuilt from reports")
e.entity("al", 30, 470, 520, "allow_range", [("list_id", "text", "PK,FK"), ("cidr", "cidr", "PK"), ("owner", "text", ""), ("reason", "text", "")],
         caption="never blocked; checked at compile and at enforcement")
e.entity("nd", 690, 470, 520, "on the node (memory + disk)", [("sorted_v4", "uint32[]", ""), ("prefix_trie", "radix", ""), ("filter", "bloom", ""),
         ("current.snap + prev.snap", "files", ""), ("version", "file", "")], kind="redis", caption="two copies at a swap; last known good on disk")
e.rel("rule", "ver", "N", "1", src="r:0.5", dst="l:0.3", label="added_version", at=(620, 120))
e.note(1250, 330, 330, "Rollback = new higher version. Never reuse a number.")
e.note(30, 745, 1540, "Tombstones live for the delta window (24 h). A node older than that takes a snapshot, which has none, so nothing is resurrected.")
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

def sizes():
    p = [T(40, 44, "Memory for the list on one node (budget: 512 MB)", 28, INK, 800)]
    x0, W = 380, 1100
    sc = W / 1800
    rows = [("IPv4 exact, 10 M × 4 B", 40, GREEN, "40 MB"), ("Prefix trie, 2 M ranges", 80, GREEN, "80 MB"),
            ("Bloom filter, 100 M × 10 bits", 125, BLUE, "125 MB"), ("IPv6 exact, 100 M × 17 B", 1700, RED, "1.7 GB")]
    for i, (lab, mb, col, txt) in enumerate(rows):
        y = 100 + i * 80
        p += [T(40, y + 34, lab, 24, INK, 700), R(x0, y, mb * sc, 50, "#e7f4ec" if col == GREEN else ("#dbeafe" if col == BLUE else "#fdecea"), col), T(x0 + mb * sc + 14, y + 35, txt, 24, col, 800)]
    p += [L(x0 + 512 * sc, 80, x0 + 512 * sc, 430, AMBER, 3, True), T(x0 + 512 * sc + 10, 440, "512 MB budget", 22, AMBER, 800)]
    (OUT / "sizes.svg").write_text(svgdoc(1600, 480, "".join(p)))
sizes()

def fanout():
    p = [T(40, 44, "Without a tree, 100,000 full downloads. With one, the origin serves 20.", 28, INK, 800)]
    cols = [("Origin", 1, 120, "#e6dcfb", PURPLE), ("Regional relays", 20, 520, "#dbeafe", BLUE), ("Zone relays", 200, 920, "#dbeafe", BLUE), ("Nodes", 100000, 1320, "#d3f3e6", GREEN)]
    for lab, n, x, fill, col in cols:
        p += [R(x, 150, 220, 130, fill, col, rx=12), T(x + 110, 205, lab, 24, INK, 800, "middle"), T(x + 110, 250, f"{n:,}", 30, col, 800, "middle")]
    for a, b2 in ((340, 520), (740, 920), (1140, 1320)):
        p.append(L(a, 215, b2, 215, GREY, 3))
    p += [T(430, 190, "×20", 22, INK, 700, "middle"), T(830, 190, "×10 each", 22, INK, 700, "middle"), T(1230, 190, "×500 each", 22, INK, 700, "middle")]
    p += [T(40, 360, "Snapshot 40 MB.  Direct: 100,000 × 40 MB = 4 TB.  Through the tree: origin → 20 regionals = 800 MB.", 25, INK, 700),
          T(40, 410, "Zone relays cache immutable, content-addressed files, so 500 nodes cost one fetch.", 25, "#57606a", 600),
          T(40, 460, "A manifest poll is about 100 bytes: 10,000 polls a second is about 1 MB a second across the fleet.", 25, "#57606a", 600)]
    (OUT / "fanout.svg").write_text(svgdoc(1600, 510, "".join(p)))
fanout()

def chain():
    p = [T(40, 44, "Versions form a chain: each checksum covers its content and the one before", 28, INK, 800)]
    xs = [60, 460, 860, 1260]
    labs = ["8,360,998", "8,360,999", "8,361,000", "8,361,001"]
    for x, lb in zip(xs, labs):
        p += [R(x, 110, 280, 110, "#d3f3e6", GREEN, rx=12), T(x + 140, 156, "version " + lb, 22, INK, 800, "middle"), T(x + 140, 196, "checksum = H(prev, content)", 19, "#173d24", 600, "middle")]
    for a in (340, 740, 1140):
        p.append(L(a, 165, a + 120, 165, GREEN, 3.5))
    p += [R(60, 290, 1480, 60, "#dbeafe", BLUE, True), T(800, 330, "delta window: the last 24 h of deltas (≈ 130 MB at the burst rate)", 24, "#0b2540", 800, "middle")]
    p += [T(60, 420, "Node has 8,360,998:", 24, INK, 800), T(330, 420, "inside the window → three small deltas, each verified before it is applied.", 24),
          T(60, 470, "Node older than the window, or a checksum fails:", 24, RED, 800), T(740, 470, "one full snapshot, verified, then swapped.", 24)]
    (OUT / "chain.svg").write_text(svgdoc(1600, 520, "".join(p)))
chain()

def badpush():
    p = [T(40, 44, "The same pipe delivers a ban and a mistake in the same 18 seconds", 28, INK, 800)]
    X = lambda t: 260 + t * 30
    for t in range(0, 41, 5):
        p += [L(X(t), 340, X(t), 352, GREY, 2), T(X(t), 380, f"{t}", 20, "#57606a", 500, "middle")]
    p.append(L(X(0), 346, X(40), 346, GREY, 2)); p.append(T(40, 410, "seconds after 14:00:00", 20, "#57606a", 600))
    p += [T(40, 120, "No gates", 26, RED, 800), R(X(0), 100, X(3) - X(0), 40, "#e6dcfb", PURPLE), T(X(1.5), 92, "compile", 18, PURPLE, 700, "middle"),
          R(X(3), 100, X(12) - X(3), 40, "#dbeafe", BLUE), T(X(7.5), 92, "relays", 18, BLUE, 700, "middle"),
          R(X(12), 100, X(21) - X(12), 40, "#fdecea", RED), T(X(16.5), 92, "all 100,000 nodes apply", 18, RED, 700, "middle"),
          R(X(21), 100, X(40) - X(21), 40, "#c8341f", RED), T(X(30.5), 128, "8 % of requests denied", 22, "#fff", 800, "middle")]
    p += [T(40, 250, "Canary", 26, GREEN, 800), R(X(0), 230, X(3) - X(0), 40, "#e6dcfb", PURPLE),
          R(X(3), 230, X(12) - X(3), 40, "#dbeafe", BLUE), R(X(12), 230, X(21) - X(12), 40, "#fdecea", RED),
          T(X(16.5), 222, "5,000 nodes only", 18, RED, 700, "middle"), R(X(21), 230, X(31) - X(21), 40, "#fdf3e1", AMBER),
          T(X(26), 258, "gate trips: halt", 22, "#4a3207", 800, "middle"), R(X(31), 230, X(40) - X(31), 40, "#d3f3e6", GREEN), T(X(35.5), 258, "rollback", 22, "#0d3b2a", 800, "middle")]
    p += [T(40, 470, "A one-line change passed review. The gate, the allowlist and a local circuit breaker are the second line.", 25, "#5a1308", 700)]
    (OUT / "badpush.svg").write_text(svgdoc(1600, 520, "".join(p)))
badpush()

def bloom():
    p = [T(40, 44, "A filter in front: not listed is certain, maybe needs a check", 28, INK, 800)]
    p += [R(60, 130, 240, 110, "#dbeafe", BLUE, rx=12), T(180, 195, "request", 26, INK, 800, "middle"),
          R(420, 130, 300, 110, "#fdf3e1", AMBER, rx=12), T(570, 178, "local filter", 26, INK, 800, "middle"), T(570, 214, "125 MB, ~1 % false positives", 19, "#4a3207", 600, "middle"),
          R(880, 40, 300, 90, "#d3f3e6", GREEN, rx=12), T(1030, 96, "not listed: allow", 24, "#0d3b2a", 800, "middle"),
          R(880, 240, 300, 110, "#e6dcfb", PURPLE, rx=12), T(1030, 290, "exact lookup tier", 24, INK, 800, "middle"), T(1030, 324, "sharded, regional", 19, "#2a1d66", 600, "middle"),
          R(1300, 240, 260, 110, "#fdecea", RED, rx=12), T(1430, 288, "listed: deny", 24, "#5a1308", 800, "middle"), T(1430, 322, "else allow, cache", 19, "#5a1308", 600, "middle")]
    p += [L(300, 185, 420, 185, INK, 3), L(720, 160, 880, 90, GREEN, 3), L(720, 210, 880, 285, PURPLE, 3), L(1180, 295, 1300, 295, RED, 3)]
    p += [T(800, 130, "99 %", 22, GREEN, 800, "middle"), T(790, 270, "~1 % + true hits", 22, PURPLE, 800, "middle")]
    p += [T(60, 440, "Used alone, 1 % of 1 M requests a second is 10,000 real users blocked every second.", 25, "#5a1308", 700),
          T(60, 480, "Behind an exact check, a false positive costs one lookup, not a wrong block.", 25, "#173d24", 700)]
    (OUT / "bloom.svg").write_text(svgdoc(1600, 530, "".join(p)))
bloom()

def authority():
    p = [T(40, 44, "A slow lookup API cannot sit on the request path, and cannot cover everything", 28, INK, 800)]
    x0, W = 360, 1100
    sc = W / 20000
    p += [T(40, 150, "New addresses", 26, INK, 800), R(x0, 120, 20000 * sc, 50, "#fdecea", RED), T(x0 + 20000 * sc - 10, 155, "20,000 / s", 24, RED, 800, "end"),
          T(40, 250, "API budget", 26, INK, 800), R(x0, 220, 100 * sc, 50, "#d3f3e6", GREEN), T(x0 + 100 * sc + 14, 255, "100 / s", 24, GREEN, 800),
          T(40, 400, "200 times over. At 100 a second, a day buys 8.6 M lookups against about 50 M distinct addresses: 17 % coverage.", 24, "#5a1308", 700),
          T(40, 450, "So: mirror a bulk list if one exists; spend the budget on the highest-volume addresses; say what first-seen means.", 24, "#173d24", 700)]
    (OUT / "authority.svg").write_text(svgdoc(1600, 500, "".join(p)))
authority()

def stale():
    p = [T(40, 44, "Stale is not open: the node keeps enforcing what it has", 28, INK, 800)]
    X = lambda m: 120 + m * 5.2
    for m in (0, 15, 60, 120, 180, 240):
        p += [L(X(m), 330, X(m), 344, GREY, 2), T(X(m), 374, f"{m} min", 20, "#57606a", 500, "middle")]
    p.append(L(X(0), 337, X(240), 337, GREY, 2))
    p += [R(X(0), 120, X(15) - X(0), 60, "#d3f3e6", GREEN), T(X(7.5), 108, "fresh", 20, GREEN, 700, "middle"),
          R(X(15), 120, X(60) - X(15), 60, "#fdf3e1", AMBER), T(X(37), 208, "past 15 min: alert", 20, "#4a3207", 700, "middle"),
          R(X(60), 120, X(240) - X(60), 60, "#fdecea", RED), T(X(150), 108, "past 60 min: drain, capped at 5 %", 20, RED, 700, "middle"),
          T(40, 270, "Every stage: the node still blocks every ban it knew about. Only the newest bans are missing.", 24, INK, 700),
          T(40, 440, "The owner signs the bound and the action per list. The cap keeps a control-plane outage from becoming a fleet outage.", 24, "#57606a", 700)]
    (OUT / "stale.svg").write_text(svgdoc(1600, 490, "".join(p)))
stale()


def tension():
    p = [T(40, 44, "Freshness against blast radius: one slider, set per push", 28, INK, 800)]
    x0, x1 = 120, 1480
    p += [R(x0, 150, x1 - x0, 24, "#eef1f4", GREY, rx=12)]
    pts = [(0.08, "no gates", "18 s to everyone", RED), (0.45, "urgent ban", "one region, 60 s bake", AMBER), (0.9, "routine push", "5 % → 25 % → all, ~10 min", GREEN)]
    for f, a, bb, col in pts:
        x = x0 + (x1 - x0) * f
        p += [L(x, 120, x, 182, col, 5), T(x, 100, a, 24, col, 800, "middle"), T(x, 226, bb, 21, INK, 600, "middle")]
    p += [T(x0, 290, "Fast", 26, BLUE, 800), T(x0, 324, "a ban lands quickly", 23), T(x0, 356, "a mistake lands just as quickly", 23, RED, 700),
          T(x1, 290, "Slow", 26, BLUE, 800, "end"), T(x1, 324, "a mistake is caught on a canary", 23, "#173d24", 700, "end"),
          T(x1, 356, "a ban waits for the bake", 23, RED, 700, "end")]
    p += [R(x0, 410, x1 - x0, 80, "#fdf3e1", AMBER), T((x0 + x1) / 2, 460, "The pipe cannot tell a ban from a mistake. The owner picks the position, per push.", 27, "#4a3207", 800, "middle")]
    (OUT / "tension.svg").write_text(svgdoc(1600, 530, "".join(p)))
tension()


print(sorted(p.name for p in OUT.glob("*.svg")))
