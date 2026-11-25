#!/usr/bin/env python3
"""SD-99 PlantUML diagrams (2026-11-25 format): the carried baseline as C4 containers V1 → V6, mechanism pictures (sequence, C4, ERD,
state machine), one C4 view per option, the two version objections as sequences, and the event-versus-HTTPS boundary."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
from pumlsvg import render, render_versions
OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
def P(name, src, kind, **kw): render(src, OUT / f"{name}.svg", kind=kind, **kw)
def I(since, alias, line, until=None): return dict(since=since, alias=alias, line=line, until=until)

# ── the carried baseline: V1 → V6, drawn once as a list, shown as deltas ───────────────────────────
render_versions("hld", [
  I(1, "pro", 'Container(pro, "Producers", "", "origination, servicing")'),
  I(1, "mer", 'System_Ext(mer, "Merchant endpoint", "POS, ERP, bank")'),
  I(2, "rel", 'Container(rel, "Outbox relay", "", "row to log")'),
  I(2, "log", 'ContainerDb(log, "Event log", "", "by loan, 7 days", $tags="store")'),
  I(2, "dsp", 'Container(dsp, "Dispatcher", "", "workers")'),
  I(3, "fan", 'Container(fan, "Fan-out", "", "match, write rows")'),
  I(3, "dst", 'ContainerDb(dst, "Delivery store", "", "a row each", $tags="store")'),
  I(3, "att", 'ContainerDb(att, "Attempt log", "", "every try", $tags="store")'),
  I(3, "api", 'Container(api, "Webhooks API", "", "logs, replay")'),
  I(4, "hl", 'Container(hl, "Endpoint health", "", "breaker, ramp")'),
  I(5, "egr", 'Container(egr, "Egress proxy", "", "public IPs only")'),
  I(6, "reg", 'Container(reg, "Renderer", "", "pinned versions")'),
  I(1, None, 'https(pro, mer, "POST [HTTPS]")', until=2),
  I(2, None, 'Rel(pro, rel, "rows")'), I(2, None, 'ev(rel, log, "publish")'),
  I(2, None, 'ev(log, dsp, "consume [event]")', until=3), I(2, None, 'https(dsp, mer, "POST [HTTPS]")', until=5),
  I(3, None, 'ev(log, fan, "consume")'), I(3, None, 'Rel(fan, dst, "rows")'), I(3, None, 'Rel(dst, dsp, "claim")'),
  I(3, None, 'Rel(dsp, att, "tries")'), I(3, None, 'Rel(api, att, " ")'), I(3, None, 'Rel(api, dst, " ")'),
  I(4, None, 'Rel(att, hl, "outcomes")'), I(4, None, 'Rel(hl, dst, "pause")'),
  I(5, None, 'Rel(dsp, egr, "signed")'), I(5, None, 'https(egr, mer, "POST [HTTPS]")'),
  I(6, None, 'Rel(fan, reg, "render")'),
], OUT, versions=(1, 2, 3, 4, 5, 6), keep={4: ["att", "hl", "dst", "dsp"], 5: ["dsp", "egr", "mer"], 6: ["log", "fan", "reg", "dst"]})

# ── the boundary: events inside, HTTPS to the endpoint ─────────────────────────────────────────────
P("hld-boundary", """
Person(dev, "Merchant developer")
Container(pro, "Producers", "", "commit the loan")
Container(rel, "Outbox relay", "", "row to log")
ContainerDb(log, "Event log", "", "durable", $tags="store")
Container(fan, "Fan-out", "", "one row per endpoint")
Container(dsp, "Dispatcher", "", "signs and sends")
Container(api, "Webhooks API", "", "register, replay")
System_Ext(mer, "Merchant endpoint", "we do not control")
https(dev, api, "POST /endpoints [HTTPS]")
Rel(pro, rel, "outbox row, same commit")
ev(rel, log, "Loan Booked [event]")
ev(log, fan, "consume")
Rel(fan, dsp, "delivery row")
https(dsp, mer, "POST signed [HTTPS]")
""", "c4", order=["dev", "api", "pro", "rel", "log", "fan", "dsp", "mer"])

# ── theory: one picture per mechanism, of the type that fits ───────────────────────────────────────
P("m-outbox", """
participant Producer
participant "Producer DB" as DB
participant Relay
participant "Event log" as L
Producer -> DB : one transaction: loan row + outbox row
DB --> Producer : commit
Relay -> DB : read unsent rows
Relay -> L : publish, keyed by loan
L --> Relay : ack
Relay -> DB : mark sent only after the ack
""", "seq")
P("m-log", """
Container(p, "Outbox relay", "", "appends once")
ContainerDb(l, "Event log", "", "key = loan, 7 days", $tags="store")
Container(g1, "Fan-out group", "", "own offset")
Container(g2, "Audit group", "", "own offset")
ev(p, l, "append [event]")
ev(l, g1, "read [event]")
ev(l, g2, "read [event]")
""", "c4", order=["p", "l", "g1", "g2"])
P("m-queue", """
entity "endpoint" as e {
  * endpoint_id
  --
  * tier
  * inflight_cap
  * state  <<open | paused>>
}
entity "delivery" as d {
  * delivery_id
  --
  * endpoint_id  <<FK>>
  * event_id
  * next_attempt_at
  * status
  * lease_until
}
entity "attempt" as a {
  * attempt_id
  --
  * delivery_id  <<FK>>
  * outcome
}
e ||--o{ d : "queue = rows by endpoint"
d ||--o{ a : "every try"
""", "erd", order=["e", "d", "a"])
P("m-breaker", """
[*] --> CLOSED
CLOSED --> OPEN : 5 failures
OPEN --> PROBING : one probe a minute
PROBING --> OPEN : probe fails
PROBING --> RAMPING : probe succeeds
RAMPING --> CLOSED : cap reached
RAMPING --> OPEN : failures again
""", "state", order=[("CLOSED",), ("OPEN",), ("PROBING",), ("RAMPING",)])
P("m-contract", """
participant Dispatcher
participant "Merchant endpoint" as M
Dispatcher -> M : POST, id evt_91, seq 7, signature
M -> M : verify the signature and the timestamp
M --> Dispatcher : 200 (processed)
Dispatcher -> M : retry: same id evt_91
M --> Dispatcher : 200 (seen: not applied twice)
Dispatcher -> M : event seq 6 arrives late
M --> Dispatcher : 200 (older than state: ignored)
""", "seq")
P("m-egress", """
Container(d, "Dispatcher", "", "signed request")
Container(x, "Egress proxy", "", "resolves the name itself")
Container(c, "Range check", "", "refuses private ranges")
System_Ext(m, "Merchant endpoint", "the checked address")
Rel(d, x, "send")
Rel(x, c, "check")
https(x, m, "connect to that address [HTTPS]")
""", "c4", order=["d", "x", "c", "m"])

# ── options: one C4 view each ──────────────────────────────────────────────────────────────────────
P("opt-a", """
Container(r, "Booking request", "", "holds a worker")
System_Ext(m, "Merchant endpoint", "30 s at a till")
https(r, m, "POST inside the request [HTTPS]")
""", "c4", order=["r", "m"])
P("opt-b", """
Container(p, "Producers", "", "enqueue")
ContainerDb(q, "One shared queue", "", "worker pool", $tags="store")
System_Ext(m1, "Slow endpoint", "10 s")
System_Ext(m2, "Healthy endpoint", "50 ms")
ev(p, q, "enqueue [event]")
https(q, m1, "all workers stuck here [HTTPS]")
https(q, m2, "waits behind it [HTTPS]")
""", "c4", order=["p", "q", "m1", "m2"])
P("opt-c", """
Container(p, "Producers", "", "publish")
ContainerDb(t, "Topic, partition per endpoint", "", "retry topics by delay", $tags="store")
Container(w, "Consumers", "", "fixed retry steps")
ev(p, t, "publish [event]")
ev(t, w, "consume [event]")
""", "c4", order=["p", "t", "w"])
P("opt-d", """
ContainerDb(l, "Event log", "", "events, replayable", $tags="store")
Container(f, "Fan-out", "", "rows by endpoint")
ContainerDb(d, "Delivery rows", "", "claimed under a cap", $tags="store")
Container(w, "Dispatcher", "", "lease, signs, sends")
ev(l, f, "consume [event]")
Rel(f, d, "rows")
Rel(d, w, "claim under cap")
""", "c4", order=["l", "f", "d", "w"])
P("opt-e", """
Container(p, "Producers", "", "publish")
System_Ext(ps, "Managed pub/sub", "push subscriptions")
System_Ext(m, "Merchant endpoint", "")
ev(p, ps, "publish [event]")
https(ps, m, "push [HTTPS]")
""", "c4", order=["p", "ps", "m"])
P("opt-f", """
Container(p, "Producers", "", "emit events")
System_Ext(v, "Webhook service", "vendor, per message")
System_Ext(m, "Merchant endpoint", "")
ev(p, v, "emit [event]")
https(v, m, "deliver [HTTPS]")
""", "c4", order=["p", "v", "m"])

# ── objections to V1 and V2: the failing case as a sequence ────────────────────────────────────────
P("obj-v1", """
participant "Booking request" as B
participant "Merchant till" as T
participant "Process" as X
B -> T : POST loan.booked
T --> B : answers after 30 s, worker held
B -> X : a retry inside the request
X -> X : a deploy restarts the process
X -> X : the loan exists, the event is gone
B -> T : another booking POSTs, then rolls back
note right of T : told of a loan that does not exist
""", "seq")
P("obj-v2", """
participant "Fast endpoints" as F
participant "Shared pool" as S
participant "Slow till" as T
participant "Merchant" as M
S -> T : 120 calls a second, 10 s each
T --> S : 1,200 workers held, the pool has 600
F -> S : events for healthy merchants queue behind it
S -> S : a restart forgets every pending retry
M -> M : you never sent it
note right of M : no record of what was sent
""", "seq")
print("puml diagrams ok")
