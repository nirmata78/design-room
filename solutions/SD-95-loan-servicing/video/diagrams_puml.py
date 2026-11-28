#!/usr/bin/env python3
"""SD-95 PlantUML diagrams (2026-11-25 format): one source for the video (reveal plans) and the GitHub Markdown design.
Mechanism pictures (state · ERD · sequence · C4), one C4 view per option, the two version objections as sequences, and the
event-versus-HTTPS boundary. C4 tech lines are left empty and written into the description (18 px minimum, see pumlsvg.py)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
from pumlsvg import render

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
def P(name, src, kind, **kw): render(src, OUT / f"{name}.svg", kind=kind, **kw)

# ── mechanisms ─────────────────────────────────────────────────────────────────────────────────────
P("m-ledger", """
entity "ledger_txn" as t {
  * txn_id
  --
  * idem_key  <<unique>>
  * effective_date
  * booked_at
  * policy_version
}
entity "ledger_line" as l {
  * line_id
  --
  * txn_id  <<FK>>
  * account
  * amount_cents  <<int>>
}
entity "balance" as b {
  * loan_id, account
  --
  * cents
  * version  <<optimistic lock>>
}
t ||--|{ l : "lines sum to 0"
l }o..o| b : "same commit"
""", "erd", order=["t", "l", "b"])

P("m-states", """
[*] --> DUE
DUE --> INTENT_OPEN : claim
INTENT_OPEN --> SUBMITTED : send
SUBMITTED --> UNKNOWN : timeout
UNKNOWN --> PENDING : accepted
UNKNOWN --> DUE : never seen
SUBMITTED --> PENDING : accepted
PENDING --> SETTLED : file
SETTLED --> RETURNED : return
RETURNED --> DUE : retry
SETTLED --> [*]
""", "state", order=[("DUE", "INTENT_OPEN"), ("SUBMITTED", "UNKNOWN"), ("PENDING", "SETTLED"), "RETURNED"])

P("m-idem", """
participant Dispatcher
participant "Servicing DB" as DB
participant Processor
Dispatcher -> DB : insert txn, key ln-5531-i3-a1
DB --> Dispatcher : ok (unique key)
Dispatcher -> Processor : charge, Idempotency-Key ln-5531-i3-a1
Processor --x Dispatcher : timeout
Dispatcher -> DB : intent = UNKNOWN
Dispatcher -> Processor : query by key ln-5531-i3-a1
Processor --> Dispatcher : the first result; posting it again is a no-op
""", "seq")

P("m-queue", """
System_Boundary(s, "Schedule service") {
  Component(c, "Claimer", "", "SKIP LOCKED, 500 rows")
  Component(i, "Intent writer", "", "one open intent each")
  Component(o, "Outbox row", "", "same commit as the intent")
  Component(w, "Sweeper", "", "frees stale claims")
}
ContainerDb(db, "Servicing DB", "", "due items · intents · outbox", $tags="store")
Rel(c, db, " ")
Rel(c, i, "per row")
Rel(i, o, "same commit")
Rel(w, db, " ")
Lay_R(o, w)
""", "c4", level="component", order=["c", "db", "i", "o", "w"])

P("m-budget", """
Container(plan, "Day plan", "", "back from 14:00")
System_Boundary(d, "Dispatcher") {
  Component(tb, "Token bucket per rail", "", "90 a second")
  Component(sw, "Pause switch per rail", "", "operator and automatic")
  Component(lim, "Live limits", "", "read from the adapter")
}
System_Ext(card, "Card processor", "contract 100 a second")
Rel(plan, tb, "rate by hour")
Rel(sw, tb, "closes")
Rel(lim, tb, "lowers")
Rel(tb, card, "90 a second")
""", "c4", level="component", order=["plan", "tb", "sw", "lim", "card"])

P("m-policy", """
entity "policy_version" as p {
  * version_id
  --
  * product
  * allocation_order
  * retry_schedule
  * late_fee_rule
  * owner, approved_by
  * valid_from
}
entity "schedule_version" as s {
  * loan_id, n
  --
  * policy_version  <<FK>>
}
entity "ledger_txn" as t {
  * txn_id
  --
  * policy_version  <<FK>>
}
p ||--o{ s : "terms used"
p ||--o{ t : "rule applied"
""", "erd", order=["p", "s", "t"])

P("m-recon", """
participant "Ledger" as L
participant "Processor report" as R
participant "Bank statement" as B
participant "Reconciliation" as X
participant "Break console" as C
L -> X : expected lines for the day
R -> X : card settlements
B -> X : debits and returns
X -> X : match by reference, then amount and date window
X -> C : typed break: owner, age, amount
""", "seq")

# ── options: one C4 view each ──────────────────────────────────────────────────────────────────────
P("opt-a", """
Container(job, "Midnight cron", "", "loops over loans due today")
ContainerDb(db, "Loans DB", "", "balance column, updated in place", $tags="store")
System_Ext(rail, "Card processor", "throttles at 100 a second")
Rel(job, rail, "2,000 charges a second [HTTPS]")
Rel(job, db, "balance = balance - amount")
""", "c4", order=["job", "db", "rail"])

P("opt-b", """
Container(s, "Scheduler", "", "publishes 600,000 messages")
Container(q, "Message broker", "", "at-least-once, redelivery on crash")
Container(w, "Workers", "", "charge per message, no state machine")
System_Ext(rail, "Card processor", "")
Rel(s, q, "one message per instalment [event]")
Rel(q, w, "delivers, may redeliver [event]")
Rel(w, rail, "charge [HTTPS]")
""", "c4", order=["s", "q", "w", "rail"])

P("opt-c", """
Container(a, "Loan aggregate", "", "event-sourced, one stream per loan")
ContainerDb(log, "Event log", "", "source of truth", $tags="store")
Container(sp, "Stream processors", "", "project balances and schedules")
ContainerDb(v, "Balance views", "", "eventually consistent", $tags="store")
Rel(a, log, "append [event]")
Rel(log, sp, "consume [event]")
Rel(sp, v, "update")
""", "c4", order=["a", "log", "sp", "v"])

P("opt-d", """
Container(sch, "Schedule + collect", "", "claim, intent, outbox")
ContainerDb(db, "Servicing DB", "", "ledger · intents · outbox", $tags="store")
Container(dsp, "Dispatcher", "", "rail budget")
Container(res, "Resolver + file ingest", "", "UNKNOWN to final, returns")
Container(rec, "Reconciliation", "", "three-way, daily")
System_Ext(rail, "Rails", "card · bank")
Rel(sch, db, "one commit")
Rel(db, dsp, "outbox")
Rel(dsp, rail, "charge with key [HTTPS]")
Rel(rail, res, "answers, files")
Rel(res, db, "posts")
Rel(db, rec, " ")
""", "c4", order=[("sch", "db"), "dsp", "rail", ("res", "rec")])

P("opt-e", """
System_Ext(org, "Origination", "")
System_Ext(vend, "Vendor servicing platform", "their schedule, their ledger, their rules")
Container(gl, "Our general ledger", "", "receives a daily export")
Rel(org, vend, "Loan Booked [event]")
Rel(vend, gl, "daily export [file]")
""", "c4", order=["org", "vend", "gl"])

# ── objections to V1 and V2: the failing case as a sequence ────────────────────────────────────────
P("obj-v1", """
participant "Midnight job" as J
participant "Card processor" as C
participant "Loans DB" as D
participant "Bank" as B
J -> C : 2,000 charges a second (contract: 100)
C --> J : 95 percent throttled
J -> C : retry at once, same burst
J -> C : 08:00 ln-5531 charge
C --x J : timeout
J -> C : retry as a new charge
C --> J : charged twice
B -> J : day 3: debit returned
J -> D : balance already reduced: nowhere to post it
""", "seq")

P("obj-v2", """
participant "Bank / processor" as B
participant "Servicing DB" as D
participant "Dispatcher" as X
participant "Policy (code)" as P
B -> B : settlement and returns, days later
note right of B : nothing reads them
X -> D : 240 intents left UNKNOWN on the 1st
note right of D : nothing ends an unknown
X -> P : refund changes the schedule
note right of P : allocation and fees live in code
D -> B : our books versus the bank's
note right of D : nothing compares them
""", "seq")

# ── the boundary: events inside, HTTPS and files at the edge ───────────────────────────────────────
P("hld-boundary", """
Person(m, "Merchant")
System_Ext(org, "Origination", "loans")
System_Boundary(s, "Servicing") {
  Container(api, "Servicing API", "", "POST /refunds, GET /payoff-quote")
  Container(sch, "Schedule service", "", "schedule, intents, ledger")
  Container(dsp, "Dispatcher", "", "charges under the rail budget")
  Container(ing, "File ingest", "", "settlements, returns, statements")
}
System_Ext(card, "Card processor", "POST /v1/charges, GET by reference")
System_Ext(bank, "Bank", "debit batch out, return in")
https(m, api, "POST /refunds [HTTPS]")
ev(org, api, "Loan Booked [event]")
Rel(api, sch, "call")
ev(sch, dsp, "Payment Due [outbox event]")
https(dsp, card, "POST /v1/charges [HTTPS]")
Rel(dsp, bank, "debit batch [file, 10:30]")
Rel(bank, ing, "return [file, days later]")
""", "c4", order=["m", "org", "api", "sch", "dsp", "card", "bank", "ing"])
print("puml diagrams ok")

# ── the carried HLD baseline as C4 containers: V1 → V2 → V3, one list, deltas by version ──────────────
from pumlsvg import render_versions
def I(since, alias, line, until=None): return dict(since=since, alias=alias, line=line, until=until)
render_versions("hld", [
  I(1, "cus", 'Person(cus, "Customer")'),
  I(1, "org", 'System_Ext(org, "Origination", "loans")'),
  I(1, "api", 'Container(api, "Servicing API", "", "keys, quotes")'),
  I(1, "svc", 'Container(svc, "Scheduler", "", "collects")'),
  I(1, "db1", 'ContainerDb(db1, "Loans DB", "", "balance", $tags="store")', until=2),
  I(1, "rail", 'System_Ext(rail, "Rails", "card, bank")'),
  I(2, "db", 'ContainerDb(db, "Servicing DB", "", "ledger, outbox", $tags="store")'),
  I(2, "dsp", 'Container(dsp, "Dispatcher", "", "rail budget")'),
  I(3, "pol", 'Container(pol, "Policy", "", "terms, rules")'),
  I(3, "ing", 'Container(ing, "File ingest", "", "files")'),
  I(3, "res", 'Container(res, "Resolver", "", "unknowns")'),
  I(3, "rec", 'Container(rec, "Reconcile", "", "3-way")'),
  I(1, None, 'ev(org, api, "Loan Booked [event]")'),
  I(1, None, 'https(cus, api, "POST /refunds [HTTPS]")'),
  I(1, None, 'Rel(api, svc, "call")'),
  I(1, None, 'Rel(svc, db1, "balance")', until=2),
  I(1, None, 'https(svc, rail, "charge [HTTPS]")', until=2),
  I(2, None, 'Rel(svc, db, "one commit")'),
  I(2, None, 'ev(db, dsp, "Payment Due [outbox]")'),
  I(2, None, 'https(dsp, rail, "charge [HTTPS]")'),
  I(3, None, 'Rel(rail, ing, "files")'),
  I(3, None, 'Rel(ing, db, " ")'),
  I(3, None, 'Rel(res, rail, " ")'),
  I(3, None, 'Rel(res, db, " ")'),
  I(3, None, 'Rel(svc, pol, " ")'),
  I(3, None, 'Rel(db, rec, " ")'),
  I(3, None, 'Lay_D(rail, ing)'),
], OUT)
print("hld versions ok")
