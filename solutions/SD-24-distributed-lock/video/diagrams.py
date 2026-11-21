#!/usr/bin/env python3
"""SD-24 distributed lock service: every picture for the video and the written design -> ./svg/*.svg.
One carried baseline (declared once), numbered flows, challenge overlays, C4, sequences, ERDs, timelines.
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
b.node("client", 30, 250, 220, 130, "client", "App + lock SDK", "sessions · local deadline")
b.node("gw", 420, 250, 200, 130, "edge", "Gateway", "auth · quota · route", since=3)
b.node("lock", 830, 250, 260, 130, "service", "Lock server", "in-memory map · TTL", until=1)
b.node("grp", 830, 250, 260, 130, "data", "Consensus group", "5 replicas · majority", since=2, stack=True)
b.node("res", 1330, 250, 240, 130, "ext", "Protected resource", "database · object store · partner API")
# tags: shown only inside a challenge, a flow or the recap
b.node("fence", 1410, 112, 180, 84, "data", "Token check", since=1, tag="ch1")
b.node("proxy", 1340, 470, 230, 120, "service", "Validating proxy", "max token", tag="ch2")
b.node("epoch", 830, 470, 260, 100, "data", "Epoch store", "durable · 16-bit", shape="db", tag="ch4")
b.node("shards", 590, 470, 210, 120, "data", "Groups 2–4", "hash → slot", stack=True, tag="ch5")
b.node("waiters", 860, 128, 220, 96, "queue", "Waiters", "per name", shape="queue", tag="ch6")
b.node("metrics", 1130, 470, 180, 100, "ext", "Metrics + canary", tag="ch7")
b.node("ops", 330, 110, 200, 80, "client", "Operator", "console", tag="ops")

REQ, RESP, HB = dict(src="r:0.22", dst="l:0.22"), dict(kind="resp", src="l:0.8", dst="r:0.8"), dict(kind="async", src="r:0.5", dst="l:0.5")
b.edge("c-l", "client", "lock", "Acquire(name)", until=1, **REQ)
b.edge("l-c", "lock", "client", "granted, ttl", until=1, at=(540, 372), **RESP)
b.edge("c-g", "client", "grp", "Acquire(name)", since=2, until=2, **REQ)
b.edge("g-c", "grp", "client", "token, ttl", since=2, until=2, at=(540, 372), **RESP)
b.edge("c-gw", "client", "gw", "Acquire", **REQ)
b.edge("hb", "client", "gw", "heartbeat", at=(335, 308), **HB)
b.edge("gw-c", "gw", "client", "granted", at=(335, 372), **RESP)
b.edge("gw-g", "gw", "grp", "to leader", src="r:0.3", dst="l:0.3")
b.edge("g-gw", "grp", "gw", "token, lease", at=(725, 372), kind="resp", src="l:0.78", dst="r:0.78")
b.edge("hb2", "gw", "grp", "alive", at=(725, 318), kind="async", src="r:0.55", dst="l:0.55")
b.edge("w", "client", "res", "write + token", src="t:0.5", dst="t:0.25", via=[(140, 80), (1390, 80)], at=(760, 66), since=3)
b.edge("w1", "client", "res", "write", src="t:0.5", dst="t:0.25", via=[(140, 80), (1390, 80)], at=(760, 66), since=1, until=2)
b.edge("f", "res", "fence", "compare", src="t:0.85", dst="b:0.5", tag="ch1", at=(1450, 232))
b.edge("c-p", "client", "proxy", "write + token", src="b:0.5", dst="b:0.5", via=[(140, 650), (1455, 650)], tag="ch2", at=(760, 636))
b.edge("p-r", "proxy", "res", "forward fresh", src="t:0.5", dst="b:0.5", tag="ch2", at=(1455, 432))
b.edge("g-e", "grp", "epoch", "epoch", src="b:0.5", dst="t:0.5", tag="ch4", kind="async", at=(990, 430))
b.edge("gw-s", "gw", "shards", "slot map", src="b:0.8", dst="t:0.25", tag="ch5", at=(540, 425))
b.edge("g-w", "grp", "waiters", "hand-off", src="t:0.5", dst="b:0.5", tag="ch6", at=(1135, 238))
b.edge("g-m", "grp", "metrics", "", src="b:0.85", dst="t:0.5", via=[(1051, 425), (1220, 425)], tag="ch7", kind="async")
b.edge("o-gw", "ops", "gw", "ForceRevoke", src="r", dst="t:0.3", via=[(580, 150)], tag="ops", at=(560, 210))

def sv(name, h, **view):
    b.h = h
    b.save(OUT / name, **view)
sv("base-v1.svg", 450, upto=1, legend=True)
sv("base-v2.svg", 450, upto=2, new=2, legend=True)
sv("base-v3.svg", 450, upto=3, new=3, legend=True)
sv("base-final.svg", 740, upto=3, show=["ch1", "ch2", "ch4", "ch5", "ch6", "ch7"], legend=True)
sv("map.svg", 740, upto=3, show=["ch1", "ch2", "ch4", "ch5", "ch6", "ch7"], legend=True,
       attack=["client", "res", "grp", "gw"], keep=None)
# one flow per functional requirement
sv("flow-fr1.svg", 520, upto=3, flow=["c-gw", "gw-g", "g-gw", "gw-c"],
       notes=[(830, 420, 520, "Leader appends, a majority acknowledges, the entry commits. Token = log index of the entry.", "blue")])
sv("flow-fr2.svg", 520, upto=3, flow=["hb", "hb2"],
       notes=[(830, 420, 560, "The leader notes liveness in memory. The SDK moves its deadline from the time it sent the beat.", "blue")])
sv("flow-fr3.svg", 520, upto=3, flow=["c-gw", "gw-g", "g-gw", "gw-c"],
       notes=[(830, 420, 560, "Release by token. Commit frees the name and hands it to the head waiter in the same step.", "blue")])
sv("flow-fr4.svg", 520, upto=3, show=["ch1"], flow=["w", "f"],
       notes=[(560, 420, 640, "Resource: reject if the token is smaller than the highest accepted. Equal is fine.", "blue")])
sv("flow-fr5.svg", 520, upto=3, show=["ops"], flow=["o-gw", "gw-g", "g-gw"],
       notes=[(830, 420, 560, "Audited. The next grant gets a higher token, so the revoked holder is fenced.", "blue")])
# challenges: the same picture, one box under attack, then one fix
sv("ch1-attack.svg", 420, upto=3, attack=["res"], keep=["client", "res"], hot=["w"],
       notes=[(560, 150, 700, "A (token 41) wakes after 15 s and writes. B (token 42) already wrote. The resource accepts both.", "red")])
sv("ch1-fix.svg", 420, upto=3, show=["ch1"], fix=["fence"], keep=["client", "res", "fence"], ok=["w", "f"],
       notes=[(560, 150, 700, "The resource keeps the highest token. A's write carries 41: smaller than 42, rejected.", "green")])
sv("ch2-attack.svg", 420, upto=3, attack=["res"], keep=["client", "res"], hot=["w"],
       notes=[(560, 150, 700, "A partner API with no conditional write: there is nowhere to put the check.", "red")])
sv("ch2-fix.svg", 700, upto=3, show=["ch2"], fix=["proxy"], keep=["client", "proxy", "res"], ok=["c-p", "p-r"],
       notes=[(560, 150, 700, "A proxy keeps the highest token per resource and forwards only fresh calls.", "green")])
sv("ch3-attack.svg", 520, upto=3, attack=["client"], keep=["client", "gw", "grp"], hot=["g-gw", "gw-c"],
       notes=[(560, 420, 620, "Server sends an expiry timestamp. A slow client clock believes it for 5 s too long.", "red")])
sv("ch3-fix.svg", 520, upto=3, fix=["client"], keep=["client", "gw", "grp"], ok=["hb", "gw-c"],
       notes=[(560, 420, 620, "deadline = send time (monotonic) + 0.7 × TTL. No timestamp crosses the wire.", "green")])
sv("ch4-attack.svg", 520, upto=3, attack=["grp"], keep=["gw", "grp"], hot=["gw-g", "g-gw"],
       notes=[(520, 420, 700, "A partition leaves the old leader with two replicas and some clients. It must not grant.", "red")])
sv("ch4-fix.svg", 620, upto=3, show=["ch4"], fix=["grp", "epoch"], keep=["gw", "grp", "epoch"], ok=["g-e"],
       notes=[(1120, 420, 440, "Majority only. After a total loss: new epoch, empty state, wait one maximum lease.", "green")])
sv("ch5-attack.svg", 520, upto=3, attack=["grp"], keep=["client", "gw", "grp"], hot=["c-gw", "gw-g"],
       notes=[(520, 420, 700, "30,000 writes a second against a 15,000 ceiling. The queue grows until leases expire.", "red")])
sv("ch5-fix.svg", 620, upto=3, show=["ch5"], fix=["shards", "gw"], keep=["client", "gw", "grp", "shards"], ok=["gw-s"],
       notes=[(840, 420, 700, "Four groups by hash of the name. Shed at the gateway with retry-after.", "green")])
sv("ch6-attack.svg", 520, upto=3, attack=["grp"], keep=["gw", "grp"], hot=["gw-g"],
       notes=[(520, 420, 700, "One name at 40 attempts a second, 100 ms holds: 10 grants a second at most.", "red")])
sv("ch6-fix.svg", 520, upto=3, show=["ch6"], fix=["waiters"], keep=["gw", "grp", "waiters"], ok=["g-w"],
       notes=[(520, 420, 700, "Bounded queue. Release hands the lock to the head waiter in one step.", "green")])
sv("ch7-attack.svg", 520, upto=3, attack=["grp"], keep=["grp", "res", "client"], ghost=[],
       notes=[(520, 420, 700, "The dashboard watches the service. The promise is broken somewhere else.", "red")])
sv("ch7-fix.svg", 620, upto=3, show=["ch7", "ch1"], fix=["metrics"], keep=["grp", "metrics", "res", "fence"], ok=["g-m"],
       notes=[(520, 420, 560, "Measure the guarantee: fenced-out writes, renewal failures, hold times, elections.", "green")])
bs.budget_bar(OUT / "budget.svg", [("network in", 2, "edge"), ("batch wait", 3, "queue"), ("leader fsync", 4, "data"),
                                   ("follower round trip + fsync", 5, "data"), ("apply + reply", 1, "service"),
                                   ("network out", 2, "edge")],
              total=20, unit="ms", title="Acquire, p99 planning budget (initial target)")

# ───────────────────────────── 2 · C4 ────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.node("team", 60, 90, 300, 150, "person", "Application team", "Person", "Services that need one holder at a time.")
d.node("sre", 60, 520, 300, 150, "person", "Operator (SRE)", "Person", "Runs the service, breaks glass.")
d.node("lock", 620, 290, 360, 200, "system", "Lock service", "Software System", "Named leases, sessions, fencing tokens.")
d.node("res", 1230, 90, 320, 150, "ext", "Protected resources", "External systems", "Databases, object store, partner APIs.")
d.node("obs", 1230, 520, 320, 150, "ext", "Observability platform", "External system", "Metrics, logs, pages.")
d.edge("team", "lock", "Acquire, renew, release", "gRPC / SDK", src="r:0.8", dst="l:0.25", at=(480, 255))
d.edge("team", "res", "Write with the token", "database, HTTP", src="r:0.3", dst="l:0.4", via=[(480, 120), (480, 150)], at=(850, 128))
d.edge("sre", "lock", "Inspect, force revoke", "audited API", src="r:0.2", dst="l:0.8", at=(480, 560))
d.edge("lock", "obs", "SLIs, fenced-out counts", "metrics", src="r:0.75", dst="l:0.3", at=(1110, 520))
d.legend(40, 780, ("person", "system", "ext"))
d.save(OUT / "c4-context.svg")

d = c4.Diagram(1600, 900)
d.boundary(380, 60, 1000, 760, "Lock service", "Software System")
d.node("app", 40, 330, 270, 160, "person", "Application", "Container: JVM service", "Uses the lock SDK, owns the work.")
d.node("sdk", 400, 330, 250, 160, "container", "Lock SDK", "Library", "Session, heartbeat, local deadline, LockLost.", size=21)
d.node("gw", 740, 330, 230, 160, "container", "Gateway", "Stateless service", "Auth, quota, slot map, leader cache.", size=21)
d.node("grp", 1080, 330, 280, 160, "db", "Consensus groups", "4 × 5 replicas", "Replicated state machine, log, snapshots.", size=21, stack=True)
d.node("epoch", 1080, 640, 280, 110, "db", "Epoch store", "Durable counter", "", size=21)
d.node("res", 1120, 90, 260, 130, "ext", "Protected resource", "External", "Checks the token.")
d.node("ops", 740, 640, 230, 110, "container", "Operator console", "CLI + API", "", size=21)
d.edge("app", "sdk", "acquire(name)", "in process", src="r", dst="l", at=(350, 310))
d.edge("sdk", "gw", "Acquire, heartbeat", "gRPC", src="r", dst="l", at=(695, 310))
d.edge("gw", "grp", "propose to leader", "gRPC", src="r", dst="l", at=(1025, 310))
d.edge("grp", "epoch", "read and bump epoch", "", src="b", dst="t", at=(1220, 570))
d.edge("ops", "gw", "ForceRevoke", "", src="t", dst="b", at=(855, 580))
d.edge("app", "res", "write + token", "", src="t", dst="l", via=[(175, 155)], at=(640, 140))
d.legend(40, 850, ("person", "container", "db", "ext"))
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

seq("seq-acquire",
    [("sdk", "Lock SDK", "container"), ("gw", "Gateway", "container"), ("ld", "Leader", "db"), ("fo", "Followers", "db")],
    [("m", "sdk", "gw", "Acquire(name, requestId, maxWait)"),
     ("m", "gw", "ld", "route by hash(name) to the leader"),
     ("m", "ld", "fo", "append entry Acquire", dict(kind="async")),
     ("r", "fo", "ld", "acknowledge; a majority makes it commit"),
     ("n", "ld", "ld", "apply: name free, so grant. token = log index, say 9,001"),
     ("r", "ld", "gw", "granted, token 9,001, ttl 10 s"),
     ("r", "gw", "sdk", "granted"),
     ("n", "sdk", "sdk", "deadline = send time + 0.7 × ttl, on the monotonic clock", "green")])

seq("seq-heartbeat-loss",
    [("app", "Application", "person"), ("sdk", "Lock SDK", "container"), ("ld", "Leader", "db"), ("q", "Next waiter", "ext")],
    [("m", "sdk", "ld", "heartbeat (every 3.3 s)"),
     ("r", "ld", "sdk", "alive; deadline moves to send time + 7 s"),
     ("n", "sdk", "ld", "network drops: no reply, no beat reaches the leader", "red"),
     ("m", "sdk", "app", "deadline passed: LockLost", dict(hl=True)),
     ("n", "app", "app", "the application stops before the next side effect", "green"),
     ("m", "ld", "ld", "no beat for one ttl: propose SessionExpired"),
     ("m", "ld", "q", "commit frees the names; head waiter granted, higher token", dict(kind="async"))])

seq("seq-release-handoff",
    [("a", "Holder A (SDK)", "container"), ("ld", "Leader", "db"), ("b", "Waiter B (SDK)", "container")],
    [("m", "a", "ld", "Release(name, token 41)"),
     ("m", "ld", "ld", "commit; apply: token matches, so free it"),
     ("m", "ld", "ld", "head of the queue is B: grant, token 42", dict(hl=True)),
     ("r", "ld", "a", "released"),
     ("m", "ld", "b", "granted, token 42, ttl 10 s", dict(kind="async")),
     ("n", "ld", "ld", "one committed write, one waiter woken, no polling", "green")])

seq("seq-fence-write",
    [("app", "Application", "person"), ("res", "Protected resource", "ext")],
    [("m", "app", "res", "write(row 17, token 42)"),
     ("n", "res", "res", "stored max 41: 42 is not smaller, accept, store 42", "green"),
     ("r", "res", "app", "ok"),
     ("m", "app", "res", "write(row 17, token 41)   (a stale holder)", dict(hl=True)),
     ("n", "res", "res", "stored max 42: 41 is smaller, reject", "red"),
     ("r", "res", "app", "FencedOut, logged with both tokens, alerts", dict(hl=True))])

seq("seq-ch1-pause",
    [("a", "Holder A", "container"), ("ls", "Lock service", "db"), ("b", "Holder B", "container"), ("r", "Resource", "ext")],
    [("m", "a", "ls", "Acquire(invoice-17)"),
     ("r", "ls", "a", "token 41, ttl 10 s"),
     ("n", "a", "a", "A pauses 15 s (garbage collection)", "red"),
     ("m", "b", "ls", "Acquire(invoice-17) at t = 10.4"),
     ("r", "ls", "b", "token 42 (lease of A expired)"),
     ("m", "b", "r", "write(token 42), accepted"),
     ("m", "a", "r", "write(token 41) at t = 15.3", dict(hl=True)),
     ("r", "r", "a", "rejected: 41 is smaller than 42", dict(hl=True))])

seq("seq-ch1-claim",
    [("b", "Holder B", "container"), ("a", "Stale holder A", "container"), ("r", "Resource", "ext")],
    [("m", "b", "r", "claim(row 17, token 42)  before reading"),
     ("n", "r", "r", "stored max becomes 42", "green"),
     ("m", "a", "r", "write(row 17, token 41)", dict(hl=True)),
     ("r", "r", "a", "rejected: 41 is smaller than 42", dict(hl=True)),
     ("m", "b", "r", "read row 17"),
     ("m", "b", "r", "write(row 17, token 42, version it read)"),
     ("r", "r", "b", "ok")])

seq("seq-ch2-proxy",
    [("app", "Application", "person"), ("px", "Validating proxy", "container"), ("tt", "Token table", "db"), ("p", "Partner API", "ext")],
    [("m", "app", "px", "call(resource, payload, token 42)"),
     ("m", "px", "tt", "set max = 42 where max <= 42  (conditional)"),
     ("r", "tt", "px", "applied"),
     ("m", "px", "p", "forward the call"),
     ("r", "p", "app", "response, through the proxy"),
     ("m", "app", "px", "call(resource, payload, token 41)", dict(hl=True)),
     ("m", "px", "tt", "set max = 41 where max <= 41"),
     ("r", "tt", "px", "not applied: max is 42", dict(hl=True)),
     ("r", "px", "app", "rejected, the partner never sees it", dict(hl=True))])

seq("seq-ch4-election",
    [("x", "Client X (minority side)", "ext"), ("r1", "R1 old leader, R2", "db"), ("r3", "R3, R4, R5", "db"), ("y", "Client Y (majority side)", "ext")],
    [("n", "r1", "r3", "partition: {R1, R2} cut off from {R3, R4, R5}", "red"),
     ("m", "r3", "r3", "no leader heard for 1.5 s: R3 wins term 8"),
     ("m", "y", "r3", "Acquire(x)"),
     ("r", "r3", "y", "granted, token 9,001 (majority committed it)"),
     ("m", "x", "r1", "Acquire(x)", dict(hl=True)),
     ("n", "r1", "r1", "R1 reaches 1 other replica of 5: it cannot commit", "red"),
     ("r", "r1", "x", "unavailable (fail closed), no grant", dict(hl=True)),
     ("m", "r3", "r1", "partition heals; R1 sees term 8, steps down, drops uncommitted", dict(kind="async"))])

seq("seq-ch4-recovery",
    [("op", "Operator", "person"), ("es", "Epoch store", "db"), ("g", "New group", "db"), ("sdk", "Lock SDKs", "container")],
    [("m", "op", "es", "bump epoch: 6 to 7 (durable)"),
     ("m", "op", "g", "start empty, seed token floor = epoch 7 << 48"),
     ("n", "g", "g", "quiet period: refuse grants for one maximum lease, 60 s", "amber"),
     ("m", "sdk", "g", "OpenSession, then Acquire", dict(kind="async")),
     ("r", "g", "sdk", "after 60 s: granted, token = (7 << 48) + index"),
     ("n", "sdk", "sdk", "every new token exceeds every token ever issued", "green")])

seq("seq-ch5-admission",
    [("sdk", "Lock SDK", "container"), ("gw", "Gateway", "container"), ("ld", "Leader (one group)", "db")],
    [("m", "sdk", "gw", "Acquire(name)"),
     ("n", "gw", "gw", "tenant over its quota, or the group's queue is deep", "red"),
     ("r", "gw", "sdk", "overloaded, retry-after 200 ms", dict(hl=True)),
     ("n", "sdk", "sdk", "wait 200 ms plus random jitter, then retry", "amber"),
     ("m", "sdk", "gw", "Acquire(name)  (retry)"),
     ("m", "gw", "ld", "admitted: route to the leader"),
     ("r", "ld", "sdk", "granted, token")])

seq("seq-ch6-queue",
    [("a", "Holder A", "container"), ("ld", "Leader", "db"), ("w1", "Waiter 1", "container"), ("w2", "Waiter 2", "container")],
    [("m", "w1", "ld", "Acquire(hot, maxWait 2 s)"),
     ("r", "ld", "w1", "queued, position 1"),
     ("m", "w2", "ld", "Acquire(hot, maxWait 2 s)"),
     ("r", "ld", "w2", "queued, position 2"),
     ("m", "a", "ld", "Release(hot, token 7)"),
     ("m", "ld", "w1", "granted, token 8 (one write, one waiter woken)", dict(kind="async", hl=True)),
     ("n", "ld", "w2", "cap or maxWait exceeded: contended, retry-after", "amber")])

# ───────────────────────────── 4 · data models ───────────────────────────────────────────────────────
c = er.Chen(1600, 900, size=26)
c.entity("t", 200, 120, "TENANT"); c.entity("n", 680, 120, "LOCK NAME"); c.entity("s", 200, 480, "SESSION")
c.entity("r", 1400, 120, "RESOURCE ROW"); c.entity("a", 680, 700, "AUDIT EVENT", weak=True)
c.rel("o", 440, 120, "OWNS"); c.rel("h", 440, 480, "HOLDS"); c.rel("p", 1040, 120, "PROTECTS"); c.rel("wf", 680, 400, "WAITS FOR")
c.rel("lg", 680, 560, "LOGGED AS", identifying=True)
c.attr("nm", 560, 48, "name", of="n", key=True); c.attr("ns", 800, 48, "namespace", of="n", key=True)
c.attr("ti", 200, 48, "tenant_id", of="t", key=True); c.attr("q", 340, 48, "quota", of="t")
c.attr("sid", 80, 560, "session_id", of="s", key=True); c.attr("ttl", 80, 400, "ttl", of="s")
c.attr("tok", 440, 590, "token", of="h"); c.attr("exp", 300, 620, "expires_at", of="h", derived=True)
c.attr("fence", 1400, 230, "max_token", of="r", derived=True); c.attr("rid", 1500, 48, "row_id", of="r", key=True)
c.attr("pos", 880, 400, "position", of="wf"); c.attr("ts", 840, 760, "reason", of="a", partial=True)
c.link("t", "o", "1"); c.link("o", "n", "N", total=True)
c.link("s", "h", "1"); c.link("h", "n", "N", dst="b:0.3")
c.link("s", "wf", "1", src="r:0.3", dst="l"); c.link("wf", "n", "N", dst="b:0.7")
c.link("n", "p", "1"); c.link("p", "r", "N")
c.link("n", "lg", "1", src="b:0.5", dst="t"); c.link("lg", "a", "N")
c.legend(1280, 560)
c.note(40, 790, 600, "A name has at most one holder at a time: HOLDS is 1 to N for a session, 0 or 1 per name.")
c.save(OUT / "erd-chen.svg")

e = er.ERD(1600, 800, size=22)
e.entity("held", 30, 40, 500, "held", [("name", "text", "PK"), ("owner", "text", ""), ("session_id", "bigint", "FK"),
         ("token", "bigint", "IX"), ("expires_at", "ms (log time)", "")], kind="focus", caption="~2,000 live rows; memory + log")
e.entity("ses", 690, 40, 300, "session", [("session_id", "bigint", "PK"), ("owner", "text", ""), ("ttl_ms", "int", ""),
         ("names", "set<text>", "")], caption="last beat: volatile, not in the log")
e.entity("wt", 1150, 40, 420, "waiter", [("name", "text", "PK,FK"), ("seq", "bigint", "PK"), ("session_id", "bigint", "FK"),
         ("request_id", "uuid", "UK"), ("enqueued_at", "ms", "")], caption="waiter.name refers to held.name; depth capped")
e.entity("slot", 30, 400, 500, "slot_epoch  (outside the group)", [("slot", "smallint", "PK"), ("epoch", "smallint", ""),
         ("floor_token", "bigint", "")], kind="ext", caption="durable; bumped on rebuild and on a slot move")
e.entity("row", 690, 400, 500, "invoice  (the protected resource)", [("id", "bigint", "PK"), ("amount", "numeric", ""),
         ("status", "text", ""), ("fence", "bigint", "IX")], kind="redis", caption="UPDATE ... WHERE fence <= :token")
e.rel("held", "ses", "N", "1", src="r:0.5", dst="l:0.3", label="session_id", at=(610, 120))
e.rel("wt", "ses", "N", "1", src="l:0.5", dst="r:0.3", label="session_id", at=(1070, 120))
e.note(1230, 400, 340, "Token = epoch << 48 | log index. 16 + 48 bits.")
e.note(30, 640, 1540, "Locks are independent per name, so every row lives in exactly one group: hash(name) → slot (0 to 63) → group. No cross-group transactions.")
e.save(OUT / "erd-physical.svg")

# ───────────────────────────── 5 · timelines and small figures ───────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start", it=False):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" '
            f'fill="{fill}"{" font-style=\"italic\"" if it else ""}>{esc(s)}</text>')
def R(x, y, w, h, fill, stroke, dash=False, rx=8, sw=2.2):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"{" stroke-dasharray=\"10 6\"" if dash else ""}/>')
def L(x1, y1, x2, y2, col=INK, sw=2.4, dash=False):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}"{" stroke-dasharray=\"8 6\"" if dash else ""}/>'

def pause_timeline(name, fenced):
    X = lambda t: 250 + t * 78
    p = [T(40, 44, "Seconds since A acquired", 22, "#57606a", 600)]
    for t in range(0, 17, 2):
        p += [L(X(t), 380, X(t), 392, GREY, 2), T(X(t), 420, f"{t}", 20, "#57606a", 500, "middle")]
    p.append(L(X(0), 386, X(16), 386, GREY, 2))
    rows = {"A": 110, "L": 200, "B": 290, "R": 360}
    for k, lab in (("A", "Holder A"), ("L", "A's lease"), ("B", "Holder B")):
        p.append(T(40, rows[k] + 9, lab, 26, INK, 700))
    p.append(T(40, 359 + 9, "Resource", 26, INK, 700))
    p += [R(X(0), 90, X(0.3) - X(0), 40, "#d3f3e6", GREEN), T(X(0.15), 78, "token 41", 20, GREEN, 700, "middle")]
    p += [R(X(0.3), 94, X(15.3) - X(0.3), 32, "#fdecea", RED, True), T(X(8), 118, "paused: garbage collection, 15 s", 24, "#5a1308", 700, "middle")]
    p += [R(X(15.3), 90, X(16) - X(15.3), 40, "#fdecea", RED), T(X(15.65), 78, "writes 41", 20, RED, 700, "middle")]
    p += [R(X(0), 182, X(10) - X(0), 36, "#dbeafe", BLUE), T(X(5), 207, "valid for 10 s", 22, "#0b2540", 600, "middle"),
          L(X(10), 160, X(10), 330, RED, 2.6, True), T(X(10) - 8, 166, "expires", 20, RED, 700, "end")]
    p += [R(X(10.4), 272, X(16) - X(10.4), 36, "#d3f3e6", GREEN), T(X(13.2), 297, "holds the lock, token 42", 22, "#0d3b2a", 600, "middle"),
          T(X(10.4), 262, "acquires", 20, GREEN, 700, "middle")]
    p += [f'<circle cx="{X(10.5):.1f}" cy="360" r="14" fill="{GREEN}"/>', T(X(10.5), 340, "write 42: accepted", 20, GREEN, 700, "middle")]
    if fenced:
        p += [f'<circle cx="{X(15.3):.1f}" cy="360" r="14" fill="{RED}"/>',
              T(X(15.3), 340, "write 41: REJECTED", 20, RED, 800, "middle"),
              L(X(15.3) - 8, 352, X(15.3) + 8, 368, "#fff", 3), L(X(15.3) - 8, 368, X(15.3) + 8, 352, "#fff", 3),
              T(40, 470, "The resource remembers 42. A smaller token is refused, whatever the lock service believes.", 25, "#173d24", 700)]
    else:
        p += [f'<circle cx="{X(15.3):.1f}" cy="360" r="14" fill="{RED}"/>', T(X(15.3), 340, "write 41: accepted", 20, RED, 800, "middle"),
              T(40, 470, "Two writers, one lock service that did nothing wrong. Nothing at the resource tells them apart.", 25, "#5a1308", 700)]
    (OUT / f"{name}.svg").write_text(svgdoc(1600, 500, "".join(p)))
pause_timeline("pause-unfenced", False)
pause_timeline("pause-fenced", True)

def ttl_slider():
    p = [T(40, 44, "Choosing the lease length (TTL): the same trade at every setting", 28, INK, 800)]
    x0, x1 = 120, 1480
    X = lambda v: x0 + (x1 - x0) * (v - 1) / 59
    p += [R(x0, 150, x1 - x0, 24, "#eef1f4", GREY, rx=12)]
    for v in (1, 5, 10, 20, 30, 60):
        p += [L(X(v), 150, X(v), 182, GREY, 2), T(X(v), 212, f"{v} s", 22, "#57606a", 600, "middle")]
    p += [L(X(10), 100, X(10), 150, GREEN, 4), T(X(10), 92, "default 10 s", 22, GREEN, 800, "middle")]
    p += [L(X(15), 100, X(15), 150, RED, 4), T(X(15) + 14, 92, "the 15 s pause", 22, RED, 800)]
    p += [T(x0, 270, "Short TTL", 26, BLUE, 800), T(x0, 304, "a crash frees its name fast", 23), T(x0, 336, "a slow holder is expired while alive", 23, RED, 700),
          T(x1, 270, "Long TTL", 26, BLUE, 800, "end"), T(x1, 304, "a crash stalls its name for a long time", 23, RED, 700, "end"),
          T(x1, 336, "fewer false expiries", 23, INK, 500, "end")]
    p += [R(x0, 390, x1 - x0, 80, "#fdecea", RED), T((x0 + x1) / 2, 440, "No setting removes the pause. A 70 s pause beats a 60 s TTL. Only a check at the resource does.",
                                                      27, "#5a1308", 800, "middle")]
    (OUT / "ttl-slider.svg").write_text(svgdoc(1600, 520, "".join(p)))
ttl_slider()

def clock_skew(name, fixed):
    X = lambda t: 220 + t * 80
    p = [T(40, 44, "Lease of 10 s, granted at server time 0" + (" · client uses durations" if fixed else " · client compares timestamps"), 26, INK, 800)]
    for t in range(0, 17, 2):
        p += [L(X(t), 300, X(t), 312, GREY, 2), T(X(t), 340, f"{t}", 20, "#57606a", 500, "middle")]
    p.append(L(X(0), 306, X(16), 306, GREY, 2))
    p += [T(40, 124, "Server", 26, INK, 700), T(40, 224, "Client", 26, INK, 700)]
    p += [R(X(0), 100, X(10) - X(0), 40, "#dbeafe", BLUE), T(X(5), 128, "server: lease valid", 22, "#0b2540", 600, "middle"),
          L(X(10), 80, X(10), 296, RED, 2.6, True), T(X(10), 72, "server expires, grants B", 20, RED, 700, "middle")]
    if not fixed:
        p += [R(X(0), 200, X(15) - X(0), 40, "#fdecea", RED), T(X(7.5), 228, "client clock 5 s slow: believes it holds until its own 10 s", 22, "#5a1308", 700, "middle"),
              R(X(10), 250, X(15) - X(10), 36, "#c8341f", RED), T(X(12.5), 276, "two holders", 22, "#ffffff", 800, "middle"),
              T(40, 400, "A timestamp from the server means nothing on a client whose clock disagrees.", 25, "#5a1308", 700)]
    else:
        p += [R(X(0), 200, X(7) - X(0), 40, "#d3f3e6", GREEN), T(X(3.5), 228, "client: holds until send time + 7 s", 22, "#0d3b2a", 700, "middle"),
              L(X(7), 190, X(7), 296, GREEN, 2.6, True), T(X(7), 182, "client stops", 20, GREEN, 700, "middle"),
              R(X(7), 250, X(10) - X(7), 36, "#e7f4ec", GREEN, True), T(X(8.5), 274, "3 s margin", 21, "#173d24", 700, "middle"),
              T(40, 400, "The client counts its own elapsed time and stops first. No clock reading crosses the wire.", 25, "#173d24", 700)]
    (OUT / f"{name}.svg").write_text(svgdoc(1600, 440, "".join(p)))
clock_skew("clock-skew", False)
clock_skew("clock-fixed", True)

def partition():
    p = [T(40, 44, "Five replicas, one partition", 28, INK, 800)]
    pos = {"R1": (210, 250), "R2": (210, 430), "R3": (1000, 180), "R4": (1250, 330), "R5": (1000, 480)}
    p += [R(60, 100, 420, 470, "#fdecea", RED, True, 16), T(80, 135, "minority side · term 7", 23, RED, 800),
          R(760, 100, 700, 470, "#e7f4ec", GREEN, True, 16), T(780, 135, "majority side · term 8", 23, GREEN, 800)]
    for k, (x, y) in pos.items():
        lead = k in ("R1", "R3")
        col, fill = (RED, "#ffffff") if k in ("R1", "R2") else (GREEN, "#ffffff")
        p += [f'<circle cx="{x}" cy="{y}" r="52" fill="{fill}" stroke="{col}" stroke-width="{5 if lead else 2.4}"/>', T(x, y + 9, k, 28, INK, 800, "middle")]
    p += [T(210, 330, "old leader", 22, RED, 700, "middle"), T(1000, 260, "new leader", 22, GREEN, 700, "middle"),
          T(610, 345, "cut", 26, RED, 800, "middle"),
          L(560, 120, 660, 560, RED, 5, True),
          T(40, 640, "R1 sees 2 of 5: it cannot commit, so it cannot grant. R3 sees 3 of 5: it can.", 26, "#5a1308", 700)]
    (OUT / "partition.svg").write_text(svgdoc(1600, 690, "".join(p)))
partition()

def token_bits():
    p = [T(40, 44, "One token: 64 bits, compared as a number", 28, INK, 800)]
    x0, W = 60, 1480
    p += [R(x0, 110, W * 16 / 64, 90, "#e6dcfb", PURPLE), T(x0 + W * 8 / 64, 168, "epoch · 16 bits", 28, "#2a1d66", 800, "middle"),
          R(x0 + W * 16 / 64, 110, W * 48 / 64, 90, "#d3f3e6", GREEN), T(x0 + W * 40 / 64, 168, "log index within the group · 48 bits", 28, "#0d3b2a", 800, "middle")]
    p += [T(x0, 250, "epoch changes only on a rebuild or a slot move; the index grows with every committed entry.", 24),
          T(x0, 300, "48 bits is 2.8 × 10^14 entries. At 15,000 a second that is about 600 years per epoch.", 24, "#57606a"),
          T(x0, 350, "16 bits is 65,536 rebuilds. Both limits are labelled arithmetic, not measurements.", 24, "#57606a"),
          R(x0, 400, W, 80, "#fdf3e1", AMBER), T(x0 + 20, 452, "Timestamps are not tokens (clocks go backwards). Random IDs are not tokens (no order).", 26, "#4a3207", 700)]
    (OUT / "token-bits.svg").write_text(svgdoc(1600, 520, "".join(p)))
token_bits()

def slots():
    p = [T(40, 44, "64 slots over four groups. Moving a slot bumps its epoch.", 28, INK, 800)]
    cols = [("Group 1", 0), ("Group 2", 16), ("Group 3", 32), ("Group 4", 48)]
    for gi, (g, s0) in enumerate(cols):
        y = 90 + gi * 100
        p += [T(40, y + 36, g, 26, INK, 800)]
        for i in range(16):
            x = 220 + i * 80
            moving = (g == "Group 1" and i == 5)
            fill, stroke = ("#fde3cf", "#c26a1b") if moving else ("#d3f3e6", "#1f8a63")
            p.append(R(x, y, 70, 56, fill, stroke, moving, 6, 2))
            p.append(T(x + 35, y + 36, str(s0 + i), 22, INK, 600, "middle"))
    p += [T(220, 520, "Slot 5: freeze, drain held locks (at most one maximum lease), bump the slot's epoch, then unfreeze in the new group.", 24, "#4a2a08", 700)]
    (OUT / "slots.svg").write_text(svgdoc(1600, 570, "".join(p)))
slots()

def hotkey():
    p = [T(40, 44, "One name, 100 ms holds: how much can it grant?", 28, INK, 800)]
    x0, W = 330, 1100
    sc = W / 45
    p += [T(40, 150, "Capacity", 26, INK, 800), R(x0, 120, 10 * sc, 50, "#d3f3e6", GREEN), T(x0 + 10 * sc + 14, 155, "10 grants/s  (1 ÷ 0.1 s)", 24, "#173d24", 700),
          T(40, 250, "Arriving", 26, INK, 800), R(x0, 220, 40 * sc, 50, "#fdecea", RED), T(x0 + 40 * sc + 14, 255, "40 attempts/s", 24, RED, 700),
          R(x0 + 10 * sc, 290, 30 * sc, 40, "#c8341f", RED), T(x0 + 25 * sc, 319, "30 a second too many", 22, "#fff", 800, "middle"),
          T(40, 420, "Unbounded queue: +30 waiters a second, so after 10 s a new waiter is 300 deep and waits about 30 s,", 25, "#5a1308", 700),
          T(40, 456, "which is longer than its own lease. Polling adds 600 reads a second on this one name.", 25, "#5a1308", 700)]
    (OUT / "hot-key.svg").write_text(svgdoc(1600, 500, "".join(p)))
hotkey()

def error_budget():
    p = [T(40, 44, "Error budget at 99.99 % for a 30-day month", 28, INK, 800)]
    x0, W = 60, 1480
    p += [R(x0, 110, W, 70, "#e7f4ec", GREEN), T(x0 + W / 2, 156, "259 seconds of unavailability allowed (4.3 minutes)", 28, "#173d24", 800, "middle")]
    p += [T(x0, 250, "Each election costs about 2 s for one group.", 26),
          T(x0, 300, "259 s ÷ 2 s ≈ 130 elections a group a month spend all of it, if nothing else fails.", 26, "#5a1308", 700),
          T(x0, 350, "So 'elections per group per day' is an SLI, and under 1 is the target.", 26, INK, 700)]
    (OUT / "error-budget.svg").write_text(svgdoc(1600, 400, "".join(p)))
error_budget()

print(sorted(p.name for p in OUT.glob("*.svg")))
