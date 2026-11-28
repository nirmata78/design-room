#!/usr/bin/env python3
"""SD-59 multi-team decomposition: PlantUML diagrams (C4 views of teams and components, sequences of the failing cases,
ERD of the contract record, a state machine of split health). Subject system: the loan-servicing platform of SD-95.
C4 tech lines are empty; the team goes in the description (18 px minimum)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
from pumlsvg import render, render_versions
OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
def P(name, src, kind, **kw): render(src, OUT / f"{name}.svg", kind=kind, **kw)
def I(since, alias, line, until=None): return dict(since=since, alias=alias, line=line, until=until)

# ── C4 level 1: the programme in its context ───────────────────────────────────────────────────────
P("ctx", """
Person(em, "You, the manager")
System(plat, "Loan-servicing platform", "5 teams, 40 engineers, 6 months")
System_Ext(a, "Origination team", "consumes our events")
System_Ext(b, "Finance ops team", "consumes our breaks")
System_Ext(r, "Card and bank rails", "external APIs")
Rel(em, plat, "owns contracts, graph, milestones")
ev(plat, a, "Loan Booked [event]")
https(b, plat, "GET /breaks [HTTPS]")
https(plat, r, "charge, batch [HTTPS]")
""", "c4", level="context", order=["em", "plat", "a", "b", "r"])

# ── the carried baseline: team-to-component map, V1 → V2 → V3 ──────────────────────────────────────
render_versions("hld", [
  I(1, "ux", 'Container(ux, "API layer", "", "Team 1, all endpoints", $tags="l1")', until=2),
  I(1, "bl", 'Container(bl, "Logic layer", "", "Team 2, all rules", $tags="l1")', until=2),
  I(1, "dl", 'ContainerDb(dl, "Data layer", "", "Team 3, all tables", $tags="store+l1")', until=2),
  I(1, "ad", 'Container(ad, "Adapter layer", "", "Team 4, all rails", $tags="l1")', until=2),
  I(1, "pf", 'Container(pf, "Platform", "", "Team 5, all infra")'),
  I(2, "core", 'Container(core, "Servicing core", "", "Team A: ledger, schedule")'),
  I(2, "col", 'Container(col, "Collections", "", "Team B: dispatch, rails")'),
  I(2, "rec", 'Container(rec, "Reconcile + files", "", "Team C: files, breaks")'),
  I(2, "api", 'Container(api, "Policy + API", "", "Team D: quotes, terms")'),
  I(3, "hub", 'Container(hub, "Contract hub", "", "schemas, tests, mocks")'),
  I(3, "sk", 'Container(sk, "Skeleton env", "", "end-to-end, week 4")'),
  I(1, None, 'Rel(ux, bl, "call")', until=2), I(1, None, 'Rel(bl, dl, "call")', until=2), I(1, None, 'Rel(bl, ad, "call")', until=2),
  I(1, None, 'Rel(pf, dl, "runs")', until=2),
  I(2, None, 'Rel(api, core, "call")'), I(2, None, 'ev(core, col, "Payment Due [event]")'), I(2, None, 'ev(col, core, "Result [event]")'),
  I(2, None, 'ev(rec, core, "Settled [event]")'), I(2, None, 'Rel(pf, core, "runs")'),
  I(3, None, 'Rel(hub, api, "contract")'), I(3, None, 'Rel(hub, col, "contract")'), I(3, None, 'Rel(sk, hub, "uses")'),
], OUT)
for v in (1, 2, 3):   # layer teams use a muted tag in V1; nothing to add: plain boxes
    pass

# ── theory: one picture per mechanism, of the type that fits ───────────────────────────────────────
P("m-seams", """
Container(a, "Servicing core", "", "ledger, schedule: Team A")
Container(b, "Collections", "", "dispatch, rails: Team B")
Container(c, "Reconcile", "", "files, breaks: Team C")
Container(d, "Policy + API", "", "quotes, terms: Team D")
ev(a, b, "Payment Due [event]")
ev(c, a, "Settled [event]")
https(d, a, "POST /refunds [HTTPS]")
""", "c4", order=["a", "b", "c", "d"])

P("m-contract", """
entity "contract" as c {
  * contract_id
  --
  * owner_team
  * kind  <<event | HTTPS>>
  * compat_policy
}
entity "contract_version" as v {
  * contract_id, version
  --
  * schema_ref
  * deprecated_on
  * sunset_on
}
entity "consumer" as k {
  * consumer_team
  --
  * contract_id, version
  * test_ref
}
c ||--o{ v : "versions"
v ||--o{ k : "consumed by"
""", "erd", order=["c", "v", "k"])

P("m-cdct", """
participant "Consumer team" as K
participant "Contract hub" as H
participant "Provider CI" as P
participant "Provider team" as O
K -> H : publishes the calls it relies on
O -> P : opens a pull request: rename a field
P -> H : runs every consumer's test
H --> P : two consumers fail
P --> O : merge blocked, consumers named
O -> K : agree an additive change, old field kept
P -> H : tests pass
""", "seq")

P("m-owner", """
Container(own, "Servicing core", "", "owns ledger + schema: Team A")
Container(x, "Collections", "", "Team B")
Container(y, "Reconcile", "", "Team C")
https(x, own, "POST /txns [HTTPS]")
https(y, own, "POST /txns [HTTPS]")
""", "c4", order=["own", "x", "y"])

P("m-skel", """
Container(api, "Policy + API", "", "stub, week 1")
Container(core, "Servicing core", "", "thin, week 2")
Container(col, "Collections", "", "mock rail, week 3")
System_Ext(rail, "Rail sandbox", "week 4")
https(api, core, "book loan [HTTPS]")
ev(core, col, "Payment Due [event]")
https(col, rail, "charge [HTTPS]")
""", "c4", order=["api", "core", "col", "rail"])

P("m-health", """
[*] --> HEALTHY
HEALTHY --> FRICTION : cross-team PRs rise
FRICTION --> HEALTHY : contract fixed
FRICTION --> REVIEW : two weeks, no change
REVIEW --> RECUT : seam moved, once
REVIEW --> HEALTHY : false alarm
RECUT --> HEALTHY
""", "state", order=[("HEALTHY",), ("FRICTION",), ("REVIEW",), ("RECUT",)])

# ── options: one C4 view each ──────────────────────────────────────────────────────────────────────
P("opt-a", """
Container(t1, "API layer", "", "Team 1")
Container(t2, "Logic layer", "", "Team 2")
ContainerDb(t3, "Data layer", "", "Team 3", $tags="store")
Rel(t1, t2, "every feature [call]")
Rel(t2, t3, "every feature [call]")
""", "c4", order=["t1", "t2", "t3"])
P("opt-b", """
Container(a, "Servicing core", "", "Team A, owns ledger")
Container(b, "Collections", "", "Team B, owns dispatch")
Container(c, "Reconcile", "", "Team C, owns breaks")
ev(a, b, "Payment Due [event]")
ev(c, a, "Settled [event]")
""", "c4", order=["a", "b", "c"])
P("opt-c", """
Container(m, "One codebase", "", "all 5 teams, no owners")
ContainerDb(d, "One database", "", "any team edits any table", $tags="store")
Rel(m, d, "every change")
""", "c4", order=["m", "d"])
P("opt-d", """
Container(s1, "12 services", "", "one per entity")
Container(s2, "12 contracts", "", "each versioned")
Container(s3, "5 teams", "", "own 2 or 3 each")
Rel(s3, s1, "own")
Rel(s1, s2, "expose")
""", "c4", order=["s3", "s1", "s2"])
P("opt-e", """
Container(p, "Platform team", "", "paved road, shared tools")
Container(s1, "Stream team", "", "owns one domain end to end")
Container(s2, "Stream team", "", "owns another domain")
Rel(p, s1, "serves")
Rel(p, s2, "serves")
https(s1, s2, "contract [HTTPS]")
""", "c4", order=["p", "s1", "s2"])

# ── objections to V1 and V2: the failing case as a sequence ────────────────────────────────────────
P("obj-v1", """
participant "Product" as PR
participant "API team" as T1
participant "Logic team" as T2
participant "Data team" as T3
participant "Adapter team" as T4
PR -> T1 : feature: partial refund
T1 -> T2 : needs a new rule
T2 -> T3 : needs a new column
T3 -> T4 : needs a new rail field
T4 --> PR : ships after all four, week 3
""", "seq")
P("obj-v2", """
participant "Team B" as B
participant "Team A" as A
participant "Team C" as C
participant "Everyone" as E
B -> A : needs ledger column X
C -> A : needs the same column as Y
A --> B : two incompatible changes, one table
note right of A : no owner rule, no contract
E -> E : first end-to-end run: month 5
note right of E : nothing fits
""", "seq")

# ── the alternate path ─────────────────────────────────────────────────────────────────────────────
P("alt", """
Container(m, "Modular monolith", "", "one team of 8, internal modules")
Container(c, "Module contracts", "", "interfaces in code")
Container(s, "Split later", "", "at 12 engineers or 3 hot modules")
Rel(m, c, "boundaries")
Rel(c, s, "when needed")
""", "c4", order=["m", "c", "s"])

# ── one sequence per requirement (how each part of the plan runs) ──────────────────────────────────
P("fr1", """
participant "You" as Y
participant "Domain leads" as D
participant "Teams" as T
Y -> D : list the nouns and who changes them together
D --> Y : change-together clusters
Y -> T : one team per cluster, one named owner
""", "seq")
P("fr2", """
participant "Provider" as P
participant "Consumers" as C
participant "Contract hub" as H
P -> H : draft contract, additive-only policy
C -> H : review and register their calls
H --> P : v1 agreed, week 2
""", "seq")
P("fr3", """
participant "Consumer team" as C
participant "Mock server" as M
participant "Provider team" as P
C -> M : build against the contract, week 2
P -> M : publish examples
P --> C : real service replaces the mock, month 4
""", "seq")
P("fr4", """
participant "Team A" as A
participant "Team B" as B
participant "Skeleton" as S
A -> S : thin ledger path
B -> S : mock rail path
S --> A : green end to end, week 4
""", "seq")
P("fr5", """
participant "Dashboard" as D
participant "You" as Y
participant "Teams" as T
D -> Y : cross-team PRs up, lead time up
Y -> T : two-week review of the seam
T --> Y : move one seam, once
""", "seq")

# ── challenges: break (failing case) and fix (C4 or sequence) ──────────────────────────────────────
P("bk-1", """
participant "Team A" as A
participant "Team B" as B
participant "Team C" as C
participant "Team D" as D
A -> A : builds the ledger, months 1 to 4
B -> A : waits for the ledger API
C -> A : waits for the ledger API
D -> A : waits for the ledger API
note right of A : critical path
""", "seq")
P("fx-1", """
Container(a, "Servicing core", "", "builds the ledger")
Container(h, "Contract hub", "", "ledger contract + mock")
Container(b, "Collections", "", "builds on the mock")
Container(c, "Reconcile", "", "builds on the mock")
Rel(a, h, "publishes v1, week 2")
Rel(h, b, "mock")
Rel(h, c, "mock")
""", "c4", order=["a", "h", "b", "c"])
P("bk-2", """
participant "Team C" as C
participant "Team B" as B
C -> B : needs your API in month 2
B --> C : not before month 4
C -> C : idle, or guesses the shape
C -> B : integrates in month 4
B --> C : the shape was different
""", "seq")
P("fx-2", """
Container(c, "Team C service", "", "builds against v1")
Container(h, "Contract hub", "", "consumer test")
Container(b, "Team B service", "", "real, month 4")
Rel(c, h, "registers its calls")
Rel(h, b, "runs them in CI")
""", "c4", order=["c", "h", "b"])
P("bk-3", """
participant "Team B" as B
participant "Team A, owner" as A
participant "Team C" as C
B -> A : rename column amount
C -> A : change amount to decimal
A -> A : two changes, one table
A --> B : which one first?
""", "seq")
P("fx-3", """
Container(a, "Servicing core", "", "expand, migrate, contract")
Container(b, "Team B", "", "reads view v1 then v2")
Container(c, "Team C", "", "reads view v1 then v2")
https(b, a, "ledger view [HTTPS]")
https(c, a, "ledger view [HTTPS]")
""", "c4", order=["a", "b", "c"])
P("bk-4", """
participant "Team B" as B
participant "You" as Y
participant "Team D" as D
B -> D : we need field X required
D -> B : we need it optional
B -> Y : escalates
D -> Y : escalates
Y -> Y : two hours of meetings
""", "seq")
P("fx-4", """
participant "Provider" as P
participant "Consumer" as C
participant "You" as Y
P -> C : proposal as a short decision record
C --> P : objection within 2 days
P -> C : additive change, old field kept
C --> Y : still disagree after 5 days
Y --> C : provider decides, consumer's cost recorded
""", "seq")
P("bk-5", """
participant "Reorg" as R
participant "Team C" as C
participant "Plan" as P
R -> C : team gone at month 3
C -> P : reconcile + files orphaned
P -> P : spread everyone thinner
P --> R : six teams of work, four teams
""", "seq")
P("fx-5", """
Container(a, "Servicing core", "", "Team A")
Container(b, "Collections", "", "Team B")
Container(c, "Reconcile", "", "paused to R2")
Container(h, "Contract hub", "", "contract unchanged")
Rel(a, h, "contract")
Rel(b, h, "contract")
Rel(c, h, "contract, frozen")
""", "c4", order=["a", "b", "h", "c"])
P("bk-6", """
participant "Dashboard" as D
participant "You" as Y
D -> Y : status: all green
Y -> Y : month 2, nothing integrated
D -> Y : month 5, slip of 2 months
""", "seq")
P("fx-6", """
Container(pr, "Cross-team PRs", "", "per week")
Container(lt, "Lead time", "", "idea to merged")
Container(sy, "Meeting load", "", "hours per engineer")
Container(d, "Split health", "", "green, amber, red")
Rel(pr, d, "signal")
Rel(lt, d, "signal")
Rel(sy, d, "signal")
""", "c4", order=["pr", "lt", "sy", "d"])
P("erd-owner", """
entity "team" as t {
  * team_id
  --
  * time_zone
  * size
}
entity "component" as c {
  * component_id
  --
  * owner_team  <<FK>>
}
entity "contract" as k {
  * contract_id
  --
  * provider_component  <<FK>>
  * kind  <<event | HTTPS>>
}
entity "dependency" as d {
  * consumer_component
  * contract_id
  --
  * needed_by_week
}
t ||--o{ c : "owns, exactly one"
c ||--o{ k : "provides"
k ||--o{ d : "consumed by"
""", "erd", order=["t", "c", "k", "d"])
print("puml diagrams ok")
