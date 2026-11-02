#!/usr/bin/env python3
"""C4 and sequence diagrams for the notification-platform video → ../svg/{c4-*,seq-*}.svg.
Generators: ~/.claude/skills/slide-video-kit/scripts/{c4svg,seqsvg}.py.  Run: python3 diagrams.py"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq

OUT = pathlib.Path(__file__).resolve().parent.parent / "svg"

# ── C4 level 1: system context ───────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.node("user", 640, 40, 340, 140, "person", "End user · 500 M", "Person",
       "Receives push, email and SMS; manages preferences; reads the in-app inbox.")
d.node("teams", 40, 300, 330, 170, "system", "Product teams · 20", "Software Systems",
       "Auth, Orders, Social, Payments, … send notification intents.", stack=True)
d.node("ops", 40, 600, 330, 140, "person", "Marketing ops", "Person", "Create, canary and halt campaigns.")
d.node("np", 620, 320, 380, 210, "focus", "Notification platform", "Software System",
       "Enforces consent, dedup, per-user caps and quiet hours; isolates priorities; delivers per channel.")
d.node("push", 1240, 250, 320, 130, "ext", "Push providers", "External System", "Apple APNs, Google FCM")
d.node("email", 1240, 440, 320, 130, "ext", "Email provider", "External System", "Transactional and bulk email")
d.node("sms", 1240, 630, 320, 130, "ext", "SMS aggregators · 2", "External System", "Highest cost per message")
d.edge("teams", "np", "Send intent", "HTTPS/JSON, mTLS", src="r:0.4", dst="l:0.3", at=(495, 360))
d.edge("ops", "np", "Create, canary, halt campaigns", "HTTPS", src="r:0.5", dst="l:0.8", at=(495, 625), width=200)
d.edge("user", "np", "Preferences, inbox", "HTTPS, WebSocket", src="b:0.5", dst="t:0.5", both=True, at=(810, 248))
d.edge("np", "push", "Send · receipts, 410", "HTTP/2", src="r:0.2", dst="l:0.5", both=True, at=(1120, 330))
d.edge("np", "email", "Send · bounces", "API", src="r:0.55", dst="l:0.5", both=True, at=(1120, 470))
d.edge("np", "sms", "Send · receipts, STOP", "API", src="r:0.9", dst="l:0.5", both=True, at=(1120, 640))
d.edge("push", "user", "Deliver to device", "", src="t:0.5", dst="r:0.5", via=[(1400, 110)], at=(1180, 98))
d.legend(40, 770, ("person", "system", "focus", "ext"))
d.save(OUT / "c4-context.svg")

# ── C4 level 2: containers, the send path ────────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.boundary(230, 20, 1090, 780, "Notification platform")
d.node("teams", 20, 110, 170, 140, "system", "Product teams · 20", "Software Systems", "", stack=True)
d.node("ops", 20, 420, 170, 130, "person", "Marketing ops", "Person")
d.node("prov", 1360, 110, 220, 150, "ext", "Push, email, SMS providers", "External Systems")
d.node("intake", 270, 100, 190, 130, "container", "Intake API", "Container", "auth, quota, validate")
d.node("kafka", 540, 100, 200, 130, "queue", "Intent log", "Kafka", "P0 · P1 · P2 topics")
d.node("policy", 820, 100, 190, 130, "focus", "Policy & router", "Container: stateless", "the six gates")
d.node("workers", 1090, 100, 200, 130, "container", "Channel workers", "Container", "one lane per priority")
d.node("camp", 270, 420, 190, 130, "container", "Campaign service", "Container", "expand, release")
d.node("ctl", 540, 420, 200, 130, "container", "Control plane", "Container", "kill flags, quotas")
d.node("redis", 820, 420, 190, 130, "db", "Dedup & rate", "Redis, TTL")
d.node("tpl", 1090, 420, 200, 130, "db", "Templates", "versioned")
d.node("prefs", 820, 640, 190, 120, "db", "Preferences", "KV + cache")
d.edge("teams", "intake", "intent", "mTLS", src="r:0.43", dst="l:0.5", at=(230, 135))
d.edge("intake", "kafka", "acks=all", "", src="r", dst="l", at=(500, 150))
d.edge("kafka", "policy", "consume", "", src="r", dst="l", at=(780, 150))
d.edge("policy", "workers", "allowed", "", src="r", dst="l", at=(1050, 150))
d.edge("workers", "prov", "send", "", src="r:0.5", dst="l:0.37", at=(1325, 150))
d.edge("ops", "camp", "create, halt", "", src="r:0.5", dst="l:0.5", at=(230, 455), width=70)
d.edge("camp", "kafka", "Release P2 at a capped rate", "", src="t:0.8", dst="b:0.3", via=[(422, 320), (600, 320)],
       at=(510, 300), width=260)
d.edge("camp", "ctl", "kill flag", "", src="r:0.5", dst="l:0.5", at=(500, 470))
d.edge("ctl", "policy", "flags pushed ≤ 1 s", "", src="t:0.75", dst="b:0.15", via=[(690, 360), (848, 360)],
       at=(770, 345), width=180)
d.edge("policy", "redis", "dedup, rate", "", src="b:0.62", dst="t:0.62", at=(938, 300))
d.edge("policy", "prefs", "consent, quiet hours, tokens", "", src="b:0.92", dst="r:0.5",
       via=[(995, 260), (1050, 260), (1050, 700)], at=(1170, 640), width=220)
d.edge("workers", "tpl", "render", "", src="b:0.5", dst="t:0.5", at=(1190, 330))
d.save(OUT / "c4-containers-send.svg")

# ── C4 level 2: containers, the feedback and read path ───────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.boundary(230, 20, 1090, 780, "Notification platform")
d.node("user", 20, 110, 170, 140, "person", "End user", "Person")
d.node("teams", 20, 440, 170, 130, "system", "Product teams · 20", "Software Systems", "", stack=True)
d.node("prov", 1360, 110, 220, 150, "ext", "Push, email, SMS providers", "External Systems")
d.node("inboxapi", 270, 100, 200, 130, "container", "Inbox API", "Container", "REST + WebSocket")
d.node("inbox", 570, 100, 220, 130, "db", "In-app inbox", "Cassandra", "(user, month), 90 days")
d.node("workers", 1060, 100, 220, 130, "container", "Channel workers", "Container")
d.node("dash", 270, 440, 200, 130, "container", "Tenant dashboards", "Container", "volume, suppressions, cost")
d.node("log", 570, 440, 220, 130, "db", "Delivery log", "wide-column", "every state + reason")
d.node("fb", 1060, 440, 220, 130, "focus", "Feedback ingest", "Container", "provider webhooks")
d.node("tokens", 1060, 650, 220, 110, "db", "Token registry", "in preferences")
d.edge("user", "inboxapi", "open", "HTTPS, WS", src="r:0.5", dst="l:0.5", at=(230, 150))
d.edge("inboxapi", "inbox", "read", "", src="r", dst="l", at=(520, 150))
d.edge("workers", "inbox", "Write in-app item", "", src="l", dst="r", at=(925, 150), width=200)
d.edge("workers", "prov", "send", "", src="r:0.5", dst="l:0.37", at=(1320, 150))
d.edge("prov", "fb", "Webhooks: receipts, bounces, 410, STOP", "", src="b:0.5", dst="r:0.5",
       via=[(1470, 505)], at=(1450, 380), width=200)
d.edge("fb", "log", "status + reason", "", src="l", dst="r", at=(925, 490), width=200)
d.edge("fb", "tokens", "delete dead tokens", "", src="b:0.5", dst="t:0.5", at=(1170, 615), width=200)
d.edge("log", "dash", "aggregate", "", src="l", dst="r", at=(520, 490))
d.edge("teams", "dash", "own cost", "", src="r:0.5", dst="l:0.5", at=(230, 490))
d.save(OUT / "c4-containers-feedback.svg")

# ── C4 level 3: components of Policy & router ────────────────────────────────────────────────────
d = c4.Diagram(1600, 820)
d.node("ctl", 380, 20, 190, 110, "container", "Control plane", "Container", "kill flags")
d.node("prefs", 700, 20, 600, 110, "db", "Preference store + local cache", "KV", "opt-ins, time zone, quiet hours, tokens")
d.boundary(240, 190, 1080, 330, "Policy & router", "Container")
X = [262, 412, 562, 712, 862, 1012, 1162]
names = [("cons", "Priority consumer", "one group per topic"), ("kill", "① Kill switch", "cached flag"),
         ("dedup", "② Dedup", "SET NX GET"), ("consent", "③ Consent", "category × channel"),
         ("rate", "④ Rate limit", "token bucket"), ("quiet", "⑤ Quiet hours", "defer P1/P2"),
         ("route", "⑥ Router", "cheapest channel")]
for x, (nid, t, ds) in zip(X, names):
    d.node(nid, x, 250, 128, 140, "component", t, "Component", ds, size=17)
for a, b in zip([n[0] for n in names], [n[0] for n in names][1:]):
    d.edge(a, b, "", src="r", dst="l", dashed=False)
d.node("kafka", 20, 260, 200, 120, "queue", "Intent log", "Kafka")
d.node("chan", 1350, 260, 230, 120, "container", "Channel workers", "Container", "allowed messages + channel")
d.node("redis", 540, 600, 400, 110, "db", "Dedup & rate counters", "Redis · one hash slot per user")
d.node("dq", 1010, 600, 220, 110, "db", "Delayed queue", "Redis sorted set")
d.edge("kafka", "cons", "poll", "", src="r", dst="l", at=(240, 300))
d.edge("route", "chan", "", src="r", dst="l")
d.edge("ctl", "kill", "≤ 1 s", "", src="b:0.5", dst="t:0.5", at=(476, 165))
d.edge("prefs", "consent", "", src="b:0.127", dst="t:0.5")
d.edge("prefs", "quiet", "", src="b:0.627", dst="t:0.5")
d.edge("prefs", "route", "", src="b:0.877", dst="t:0.5")
d.edge("dedup", "redis", "", src="b:0.5", dst="t:0.215", both=True)
d.edge("rate", "redis", "", src="b:0.5", dst="t:0.965", both=True)
d.edge("quiet", "dq", "defer", "", src="b:0.5", dst="t:0.3", at=(1100, 560))
d.edge("dq", "cons", "wake up → through every gate again", "", src="b:0.5", dst="b:0.5",
       via=[(1120, 770), (326, 770)], at=(720, 770), width=420)
d.note(1250, 600, 330, "Each gate that says no records SUPPRESSED or DEFERRED with the reason in the delivery log.", size=17)
d.save(OUT / "c4-component-policy.svg")

# ── Sequence: P0 password reset during a 400 M campaign ──────────────────────────────────────────
s = sq.Seq(1500, size=22, row=50, head=66)
for pid, lab, k in [("auth", "Auth service", "ext"), ("in", "Intake API", "container"), ("k", "Kafka notif.p0", "queue"),
                    ("pol", "Policy · P0 lane", "focus"), ("r", "Redis", "db"), ("w", "Push worker · P0", "container"),
                    ("apns", "Apple APNs", "ext")]:
    s.part(pid, lab, k)
s.msg("auth", "in", "POST /notifications  P0, dedupKey")
s.msg("in", "k", "produce, acks=all")
s.ret("in", "auth", "202 Accepted + id")
s.msg("k", "pol", "consume, lag ≈ 0", "async")
s.msg("pol", "r", "kill? · dedup SET NX GET")
s.ret("r", "pol", "first time")
s.msg("pol", "pol", "consent ✓ · P0 exempt from caps")
s.msg("pol", "w", "route: push", "async")
s.msg("w", "apns", "send, collapse-id = dedupKey", hl=True)
s.ret("apns", "w", "200 → SENT")
s.save(OUT / "seq-p0.svg")

# ── Sequence: idempotency and dedup ──────────────────────────────────────────────────────────────
s = sq.Seq(1500, size=22, row=48, head=66)
for pid, lab, k in [("k", "Kafka", "queue"),
                    ("a", "Policy worker A", "container"), ("b", "Policy worker B", "container"), ("r", "Redis", "db")]:
    s.part(pid, lab, k)
s.frame("alt", "worker crashes after the check: at-least-once")
s.msg("k", "a", "deliver n1", "async")
s.msg("a", "r", "SET dd:k n1 NX GET")
s.ret("r", "a", "nil → first time")
s.msg("a", "a", "crash before commit", hl=True)
s.msg("k", "b", "redeliver n1", "async")
s.msg("b", "r", "SET dd:k n1 NX GET")
s.ret("r", "b", "n1 → my own retry, proceed")
s.end()
s.frame("alt", "a different request that means the same thing: dedup")
s.msg("b", "r", "SET dd:k n2 NX GET")
s.ret("r", "b", "n1 ≠ n2 → SUPPRESSED duplicate", hl=True)
s.end()
s.save(OUT / "seq-dedup.svg")

# ── Sequence: campaign canary and release ────────────────────────────────────────────────────────
s = sq.Seq(1500, size=22, row=50, head=66)
for pid, lab, k in [("ops", "Marketing ops", "person"), ("c", "Campaign service", "container"),
                    ("k", "Kafka notif.p2", "queue"), ("p", "Policy workers", "container"),
                    ("w", "Channel workers", "container"), ("pr", "Providers", "ext")]:
    s.part(pid, lab, k)
s.msg("ops", "c", "create: segment, template, rate")
s.msg("c", "k", "canary: 0.1 % + seed list")
s.note("ops", "c", "Hold: check rendering and complaints", "amber")
s.msg("ops", "c", "approve")
s.frame("loop", "per time-zone bucket")
s.msg("c", "k", "release at ≤ 50k/s", "async", hl=True)
s.msg("k", "p", "every gate applies", "async")
s.msg("p", "w", "allowed", "async")
s.msg("w", "pr", "send")
s.end()
s.save(OUT / "seq-campaign.svg")

# ── Sequence: campaign halt ──────────────────────────────────────────────────────────────────────
s = sq.Seq(1500, size=22, row=52, head=66)
for pid, lab, k in [("ops", "Tenant / marketing ops", "person"), ("c", "Campaign service", "container"),
                    ("cp", "Control plane", "container"), ("p", "Policy workers", "container"),
                    ("w", "Channel workers", "container"), ("pr", "Providers", "ext")]:
    s.part(pid, lab, k)
s.msg("ops", "c", "HALT", hl=True)
s.msg("c", "cp", "set kill flag", hl=True)
s.msg("cp", "p", "flag pushed ≤ 1 s", hl=True)
s.msg("p", "p", "queued → SUPPRESSED (killed)")
s.msg("w", "cp", "re-check just before each send")
s.note("w", "pr", "Already sent can't be recalled. In-app items can be deleted.", "red")
s.save(OUT / "seq-halt.svg")

# ── Sequence: fallback only on a definite failure ────────────────────────────────────────────────
s = sq.Seq(1500, size=22, row=48, head=66)
for pid, lab, k in [("rt", "Router", "component"), ("pw", "Push worker", "container"), ("ap", "APNs / FCM", "ext"),
                    ("fb", "Feedback ingest", "container"), ("tk", "Token registry", "db"),
                    ("ew", "Email worker", "container"), ("ep", "Email provider", "ext")]:
    s.part(pid, lab, k)
s.msg("rt", "pw", "send push, dedupKey k")
s.msg("pw", "ap", "send")
s.frame("alt", "410 Unregistered: a definite failure")
s.ret("ap", "pw", "410")
s.msg("pw", "fb", "token dead", "async")
s.msg("fb", "tk", "delete token")
s.ret("pw", "rt", "definite failure")
s.msg("rt", "ew", "fallback: email, SAME dedupKey k", hl=True)
s.msg("ew", "ep", "send")
s.end()
s.frame("alt", "no receipt after 30 s: NOT a failure")
s.msg("rt", "rt", "wait; do not fall back", hl=True)
s.end()
s.note("rt", "ep", "Fraud alerts may go to two channels at once: a send-both decision made up front, not a fallback.", "amber")
s.save(OUT / "seq-fallback.svg")
print("diagrams →", OUT)
