#!/usr/bin/env python3
"""SD-29 device-fleet control plane: every picture for the video and the written design -> ./svg/*.svg.
One canonical container view (V1 -> V4), three component views (device agent, rollout controller, gateway), sequences,
data models, figures. Run: python3 diagrams.py"""
import html, pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import basesvg as bs
import c4svg as c4
import seqsvg as sq
import erdsvg as er
from gtheme import ink

OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
for old in OUT.glob("*"): old.unlink()
FONT = "Inter, Roboto, sans-serif"
INK, RED, GREEN, BLUE, GREY, AMBER = "#202124", "#ea4335", "#34a853", "#4285f4", "#5f6368", "#fbbc05"
def esc(s): return html.escape(str(s))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
import stack

# ───────────────────────────── 1 · the canonical container view ─────────────────────────────────────
X = dict(A=20, B=400, C=780, D=1160, E=1540); Y = dict(R0=100, R1=360, R2=620); W, H, SZ = 250, 140, 26
def P(cell): return X[cell[0]], Y[cell[1:]]
BOX = {
    "agent":   ("AR1", "container", "Device agent", "On 1 M devices", "Applies, reports.", 1),
    "gw":      ("BR1", "container", "Device gateway", "Broker", "Sessions, mTLS.", 1),
    "tele":    ("BR2", "queue", "Telemetry", "Partitioned log", "Health, every 5 min.", 2),
    "recon":   ("CR0", "container", "Reconciler", "Service", "Nudges the drift.", 2),
    "shadow":  ("CR1", "db", "Shadow store", "Database", "Desired, reported.", 1),
    "metrics": ("CR2", "db", "Metrics store", "Time series", "By cohort.", 2),
    "rollout": ("DR0", "container", "Rollout controller", "Service", "Waves, halts.", 3),
    "api":     ("DR1", "container", "Fleet API", "Service", "Operators, cohorts.", 1),
    "census":  ("DR2", "container", "Fleet census", "Service", "Versions, convergence.", 4),
    "cdn":     ("ER0", "ext", "Image CDN", "External", "Signed firmware.", 3),
    "op":      ("ER1", "person", "Operator", "Person", "Sets configs, releases.", 1),
}

def canon(labels=None):
    d = c4.Diagram(1830, 830, canon="containers")
    d.boundary(5, 20, 1430, 790, "Fleet platform", "Software System", top="left")
    for k, (cell, kind, t, typ, desc, since) in BOX.items():
        if labels and k in labels: typ, desc = labels[k][1], labels[k][2]
        x, y = P(cell)
        d.node(k, x, y, W, H, kind, t, typ, desc, size=SZ, since=since)
    E = d.edge
    E("agent", "gw", "MQTT", "mTLS", src="r:0.3", dst="l:0.3", at=(335, 380), size=21, eid="a-g")
    E("gw", "shadow", "reported", "", src="r:0.3", dst="l:0.3", at=(715, 388), size=21, eid="g-s")
    E("shadow", "gw", "desired", "", src="l:0.75", dst="r:0.75", at=(715, 470), size=21, eid="s-g")
    E("op", "api", "change", "HTTPS", src="l", dst="r", at=(1475, 412), size=21, eid="o-a")
    E("api", "shadow", "desired, v+1", "", src="l:0.5", dst="r:0.5", at=(1095, 412), size=21, eid="a-s")
    E("recon", "shadow", "drift", "", src="b:0.5", dst="t:0.5", at=(960, 300), size=21, eid="r-s", since=2)
    E("recon", "gw", "nudge", "", src="l:0.8", dst="t:0.8", via=[(600, 212)], at=(640, 270), size=21, eid="r-g", since=2)
    E("gw", "tele", "telemetry", "", src="b:0.5", dst="t:0.5", at=(590, 560), size=21, eid="g-t", since=2)
    E("tele", "metrics", "by cohort", "", src="r:0.5", dst="l:0.5", at=(715, 690), size=21, eid="t-m", since=2)
    E("api", "rollout", "release", "", src="t:0.5", dst="b:0.5", at=(1350, 300), size=21, eid="a-r", since=3)
    E("rollout", "shadow", "desired, per wave", "", src="b:0.15", dst="t:0.9", at=(1090, 268), size=21, width=200, eid="r-sh", since=3)
    E("rollout", "metrics", "wave health", "", src="l:0.85", dst="r:0.3", via=[(1095, 219), (1095, 662)], at=(1095, 520), size=21, eid="r-m", since=3)
    E("agent", "cdn", "image, signed", "", src="t:0.5", dst="t:0.5", via=[(145, 60), (1665, 60)], at=(905, 54), size=21, eid="a-c", since=3)
    E("census", "metrics", "health", "", src="l:0.7", dst="r:0.7", at=(1095, 735), size=21, eid="c-m", since=4)
    E("census", "shadow", "", "", src="t:0.2", dst="b:0.8", eid="c-s", since=4)
    d.legend(1560, 640, ("person", "container", "db", "queue", "ext"), vertical=True)
    return d

d = canon()
d.save(OUT / "base-v1.svg", upto=1, order=["agent", "gw", "shadow", "api", "op"])
d.save(OUT / "base-v2.svg", upto=2, new=2, order=["recon", "tele", "metrics"])
d.save(OUT / "base-v3.svg", upto=3, new=3, order=["rollout", "cdn"])
d.save(OUT / "base-v4.svg", upto=4, new=4, order=["census"])
d.save(OUT / "flow-config.svg", upto=3, flow=["o-a", "a-s", "r-s", "r-g", "s-g", "g-s"])
d.save(OUT / "flow-release.svg", upto=3, flow=["a-r", "r-sh", "s-g", "a-c", "g-t", "t-m", "r-m"])
d.save(OUT / "map.svg", upto=3, attack=["agent", "rollout", "shadow", "gw", "tele"], keep=None)
d.save(OUT / "ch6-attack.svg", upto=3, attack=["metrics"], keep=["gw", "tele", "metrics", "shadow"])
d.save(OUT / "recap.svg", upto=4, badges={"agent": "M4 A/B", "gw": "M2 M5", "shadow": "M1", "recon": "M1", "rollout": "M3", "census": "census"})
d.save(OUT / "alt.svg", upto=3, attack=["recon", "rollout"], keep=["agent", "gw", "shadow", "recon", "rollout", "api"])
dt = canon(stack.C4)
dt.save(OUT / "c4-containers-tech.svg", upto=3, focus=["agent", "gw", "shadow", "recon", "rollout", "tele", "metrics"], keep=None)

# ───────────────────────────── 2 · C4 context ────────────────────────────────────────────────────────
x = c4.Diagram(1600, 700)
x.node("dev", 40, 80, 320, 150, "ext", "Devices in the field", "1 M, 7-year life", "Often offline; a truck roll to fix.", size=26)
x.node("op", 40, 440, 320, 150, "person", "Operators", "Person", "Change configs, release firmware.", size=26)
x.node("sys", 620, 250, 380, 190, "system", "Fleet platform", "Software System", "Desired state, rollouts, health.", size=28)
x.node("fac", 1240, 80, 320, 150, "ext", "Factory PKI", "External system", "A key per device at manufacture.", size=26)
x.node("cdn", 1240, 440, 320, 150, "ext", "Image CDN", "External system", "Serves signed firmware.", size=26)
x.edge("dev", "sys", "state, telemetry", "MQTT, mTLS", src="r", dst="l:0.25", at=(490, 160), size=22)
x.edge("op", "sys", "desired state", "HTTPS", src="r", dst="l:0.75", at=(490, 520), size=22)
x.edge("fac", "sys", "device certificates", "registration", src="l", dst="r:0.25", at=(1120, 160), size=22)
x.edge("sys", "cdn", "publish images", "upload", src="r:0.75", dst="l", at=(1120, 520), size=22)
x.legend(40, 660, ("person", "system", "ext"))
x.save(OUT / "c4-context.svg", order=["dev", "sys", "op", "fac", "cdn"])

# ───────────────────────────── 3 · component views ───────────────────────────────────────────────────
CX = [20, 300, 560, 820, 1080, 1340, 1600]; CW, CH, CS = 210, 150, 25
def comp(name, tech):
    d = c4.Diagram(1830, 770, canon="comp:" + name)
    d.boundary(275, 40, 1300, 700, name, tech, top="left")
    return d

a = comp("Device agent", "Container: C, on the device")
a.node("gw", CX[0], 330, 200, CH, "container", "Device gateway", "Broker", "", size=CS)
a.node("mq", CX[1], 330, CW, CH, "component", "MQTT client", "Backoff", "Jitter; resumes.", size=CS)
a.node("cfg", CX[2], 330, CW, CH, "component", "Config applier", "Latest wins", "Applies, reports v.", size=CS)
a.node("upd", CX[3], 330, CW, CH, "component", "Updater", "Verify, write", "Inactive slot.", size=CS)
a.node("boot", CX[4], 330, CW, CH, "component", "Bootloader", "Boot counter", "Tries, then reverts.", size=CS)
a.node("slots", CX[5], 330, CW, CH, "db", "Slots A / B", "Flash", "Last good: A.", size=CS)
a.node("kill", CX[1], 90, CW, CH, "component", "Kill switch", "Separate path", "Signed, minimal.", size=CS)
a.node("cdn", CX[3], 90, CW, CH, "ext", "Image CDN", "External", "", size=CS)
a.node("wd", CX[4], 90, CW, CH, "component", "Watchdog", "Hardware timer", "120 s deadline.", size=CS)
a.node("buf", CX[1], 570, CW, CH, "component", "Telemetry buffer", "Store and forward", "seq per message.", size=CS)
for a_, b_ in (("gw", "mq"), ("mq", "cfg"), ("cfg", "upd"), ("upd", "boot"), ("boot", "slots")):
    a.edge(a_, b_, "", "", src="r", dst="l")
a.edge("mq", "kill", "", "", src="t", dst="b"); a.edge("cdn", "upd", "", "", src="b", dst="t")
a.edge("wd", "boot", "", "", src="b", dst="t"); a.edge("buf", "mq", "", "", src="t", dst="b")
a.legend(40, 120, ("component", "container", "db", "ext"), vertical=True)
a.save(OUT / "c4-comp-agent.svg", order=["gw", "mq", "kill", "buf", "cfg", ("upd", "cdn"), "boot", "wd", "slots"])
a.save(OUT / "ch1-attack.svg", keep=["cfg", "upd", "boot"], attack=["cfg"])
a.save(OUT / "ch1-fix.svg", keep=["upd", "boot", "slots"], fix=["boot", "slots"])
a.save(OUT / "ch3-attack.svg", keep=["mq", "cfg"], attack=["cfg"])
a.save(OUT / "ch3-fix.svg", keep=["mq", "cfg"], fix=["cfg"])
a.save(OUT / "ch5-attack.svg", keep=["buf"], attack=["buf"])
a.save(OUT / "ch5-fix.svg", keep=["buf"], fix=["buf"])

r = comp("Rollout controller", "Container: Go service")
r.node("api", CX[0], 330, 200, CH, "container", "Fleet API", "Service", "A release.", size=CS)
r.node("plan", CX[1], 330, CW, CH, "component", "Release plan", "Waves", "0.1 → 1 → 10 → 100 %.", size=CS)
r.node("coh", CX[2], 330, CW, CH, "component", "Cohort picker", "Strata", "Every hardware rev.", size=CS)
r.node("sch", CX[3], 330, CW, CH, "component", "Wave scheduler", "Soak timers", "24 h per wave.", size=CS)
r.node("cmp", CX[4], 330, CW, CH, "component", "Health comparer", "Wave vs control", "Crash rates.", size=CS)
r.node("halt", CX[5], 330, CW, CH, "component", "Halt rule", "Automatic", "Stop, then revert.", size=CS)
r.node("shadow", CX[6], 330, 210, CH, "db", "Shadow store", "PostgreSQL", "", size=CS)
r.node("met", CX[4], 90, CW, CH, "db", "Metrics store", "By cohort", "", size=CS)
r.node("gate", CX[3], 570, CW, CH, "component", "Approval gate", "A person", "Before 10 %.", size=CS)
for a_, b_ in (("api", "plan"), ("plan", "coh"), ("coh", "sch"), ("sch", "cmp"), ("cmp", "halt"), ("halt", "shadow")):
    r.edge(a_, b_, "", "", src="r", dst="l")
r.edge("met", "cmp", "", "", src="b", dst="t"); r.edge("sch", "gate", "", "", src="b", dst="t")
r.legend(40, 120, ("component", "container", "db"), vertical=True)
r.save(OUT / "c4-comp-rollout.svg", order=["api", "plan", "coh", "sch", "gate", ("cmp", "met"), "halt", "shadow"])
r.save(OUT / "ch2-attack.svg", keep=["plan", "coh", "sch"], attack=["coh"])
r.save(OUT / "ch2-fix.svg", keep=["coh", "sch", "cmp", "halt"], fix=["coh", "halt"])

g = comp("Device gateway", "Container: EMQX cluster")
g.node("dev", CX[0], 330, 200, CH, "ext", "Devices", "1 M", "", size=CS)
g.node("tls", CX[1], 330, CW, CH, "component", "TLS terminator", "mTLS", "Certificate per device.", size=CS)
g.node("adm", CX[2], 330, CW, CH, "component", "Admission", "Token bucket", "Connects per node.", size=CS)
g.node("sess", CX[3], 330, CW, CH, "component", "Sessions", "MQTT 5", "Survive 7 days.", size=CS)
g.node("cache", CX[4], 330, CW, CH, "component", "Desired cache", "By version", "Current? One compare.", size=CS)
g.node("bridge", CX[5], 330, CW, CH, "component", "Bridge", "To Kafka", "Reported, telemetry.", size=CS)
g.node("sh", CX[6], 330, 210, CH, "db", "Shadow store", "PostgreSQL", "", size=CS)
for a_, b_ in (("dev", "tls"), ("tls", "adm"), ("adm", "sess"), ("sess", "cache"), ("cache", "bridge"), ("bridge", "sh")):
    g.edge(a_, b_, "", "", src="r", dst="l")
g.legend(40, 120, ("component", "db", "ext"), vertical=True)
g.save(OUT / "c4-comp-gateway.svg", order=["dev", "tls", "adm", "sess", "cache", "bridge", "sh"])
g.save(OUT / "ch4-attack.svg", keep=["tls", "adm", "sess"], attack=["adm"])
g.save(OUT / "ch4-fix.svg", keep=["adm", "sess", "cache"], fix=["adm", "cache"])

# ───────────────────────────── 4 · sequences ─────────────────────────────────────────────────────────
def seq(name, parts, steps, size=24, row=54, width=1500):
    q = sq.Seq(width, size=size, row=row)
    for pp in parts: q.part(*pp)
    for st in steps:
        k = st[0]
        if k == "m": q.msg(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "r": q.ret(st[1], st[2], st[3], **(st[4] if len(st) > 4 else {}))
        elif k == "n": q.note(st[1], st[2], st[3], *(st[4:5]))
    q.save(OUT / f"{name}.svg")

seq("seq-report",
    [("ag", "Device agent", "container"), ("gw", "Gateway", "container"), ("sh", "Shadow store", "db"), ("tl", "Telemetry", "queue")],
    [("m", "ag", "gw", "reported: firmware 4.2, config v17"),
     ("m", "gw", "sh", "reported, reported_v 17"),
     ("m", "ag", "gw", "health summary, seq 88,120 (every 5 min)", dict(kind="async")),
     ("m", "gw", "tl", "to Kafka, keyed by device", dict(kind="async")),
     ("n", "tl", "tl", "seq ≤ last seen? drop", "amber")])

seq("seq-config",
    [("op", "Operator", "person"), ("sh", "Shadow store", "db"), ("rc", "Reconciler", "container"), ("gw", "Gateway", "container"), ("ag", "Device agent", "container")],
    [("m", "op", "sh", "desired v18 for cohort “store-eu”, if v = 17"),
     ("m", "rc", "sh", "rows where desired_v > reported_v"),
     ("m", "rc", "gw", "nudge 40,000 devices, spread over 10 min", dict(kind="async")),
     ("m", "ag", "gw", "get desired (I have v17)"),
     ("r", "gw", "ag", "v18 document"),
     ("n", "ag", "ag", "apply; on failure keep v17", "green"),
     ("m", "ag", "sh", "reported_v 18", dict(hl=True))])

seq("seq-release",
    [("rc", "Rollout ctl", "container"), ("sh", "Shadow store", "db"), ("ag", "Device agent", "container"), ("cd", "Image CDN", "ext"), ("mt", "Metrics", "db")],
    [("m", "rc", "sh", "wave 1: 1,000 devices, every hardware rev, fw 4.3"),
     ("m", "ag", "cd", "GET image by range; verify signature + SHA-256"),
     ("n", "ag", "ag", "write slot B; reboot into B; watchdog 120 s", "blue"),
     ("m", "ag", "sh", "reported fw 4.3, healthy"),
     ("m", "rc", "mt", "wave against control, 24 h"),
     ("n", "rc", "rc", "crashes 0.21 % vs 0.20 %: next wave", "green")])

seq("seq-halt",
    [("mt", "Metrics", "db"), ("rc", "Rollout ctl", "container"), ("sh", "Shadow store", "db"), ("ag", "Agents in wave 2", "container")],
    [("m", "mt", "rc", "wave 2 reconnects 3× control"),
     ("n", "rc", "rc", "halt rule fires: no new devices", "amber"),
     ("m", "rc", "sh", "desired fw back to 4.2, as v+1, for wave 2"),
     ("m", "sh", "ag", "desired 4.2", dict(kind="async")),
     ("n", "ag", "ag", "slot A still holds 4.2: switch and reboot", "green")])

seq("seq-th-ab",
    [("bl", "Bootloader", "container"), ("sb", "Slot B (new)", "db"), ("wd", "Watchdog", "container"), ("sa", "Slot A (last good)", "db")],
    [("n", "bl", "bl", "try B; tries left 3", "blue"),
     ("m", "bl", "sb", "boot 4.3"),
     ("n", "wd", "wd", "agent must confirm healthy within 120 s", "amber"),
     ("m", "wd", "bl", "no confirmation: reset (tries 2, 1, 0)"),
     ("m", "bl", "sa", "tries exhausted: boot 4.2", dict(hl=True)),
     ("n", "bl", "bl", "report: rolled back from 4.3", "green")])

seq("seq-ch1-brick",
    [("sh", "Shadow store", "db"), ("ag", "Agent", "container"), ("bl", "Bootloader", "container"), ("sa", "Slot A", "db")],
    [("m", "sh", "ag", "config v18: a bad display mode"),
     ("n", "ag", "ag", "apply v18 as pending; reboot to take it", "amber"),
     ("n", "bl", "bl", "boot crashes; watchdog resets; tries 2, 1, 0", "amber"),
     ("m", "bl", "sa", "revert to config v17 and firmware in A"),
     ("m", "ag", "sh", "reported v17, rejected v18: crash loop", dict(hl=True))])

# ───────────────────────────── 5 · data models ───────────────────────────────────────────────────────
c = er.Chen(1960, 900, size=27)
c.entity("dev", 200, 140, "DEVICE"); c.entity("coh", 700, 140, "COHORT"); c.entity("des", 200, 560, "DESIRED DOC", weak=True)
c.entity("rep", 700, 560, "REPORTED DOC", weak=True); c.entity("rel", 1200, 140, "RELEASE"); c.entity("img", 1200, 560, "IMAGE")
c.rel("in", 450, 140, "IN"); c.rel("tgt", 950, 140, "TARGETS"); c.rel("has", 200, 350, "WANTS", identifying=True)
c.rel("rp", 450, 560, "REPORTS", identifying=True); c.rel("ships", 1200, 350, "SHIPS")
c.attr("did", 200, 50, "device_id", of="dev", key=True); c.attr("hw", 420, 50, "hw_rev", of="dev")
c.attr("cid", 700, 50, "cohort", of="coh", key=True)
c.attr("dv", 60, 680, "version", of="des", partial=True); c.attr("rv", 700, 680, "version", of="rep", partial=True)
c.attr("sha", 1460, 560, "sha256", of="img", key=True); c.attr("w", 1460, 140, "waves", of="rel")
c.link("dev", "in", "N"); c.link("in", "coh", "1")
c.link("coh", "tgt", "N"); c.link("tgt", "rel", "M")
c.link("dev", "has", "1", src="b", dst="t"); c.link("has", "des", "N", src="b", dst="t", total=True)
c.link("des", "rp", "", src="r", dst="l"); c.link("rp", "rep", "N", total=True)
c.link("rel", "ships", "1", src="b", dst="t"); c.link("ships", "img", "1", src="b", dst="t")
c.legend(1660, 300, size=23, gap=36, rows=["rect", "rect2", "dia", "dia2", "oval", "key", "dbl"])
c.save(OUT / "erd-chen.svg", order=["dev", ("coh", "in"), ("des", "has"), ("rep", "rp"), ("rel", "tgt"), ("img", "ships")])

e = er.ERD(1600, 820, size=22)
e.entity("dev", 30, 40, 470, "device", [("device_id", "text", "PK"), ("cohort", "text", "IX"), ("hw_rev", "text", ""),
         ("desired_v", "bigint", ""), ("reported_v", "bigint", ""), ("seen_at", "ts", "")], kind="focus", caption="1 M rows; drift = desired_v > reported_v")
e.entity("des", 570, 40, 470, "desired_doc", [("device_id", "text", "PK"), ("version", "bigint", "PK"), ("doc", "jsonb", ""), ("author", "text", "")],
         caption="append-only history")
e.entity("rel", 1110, 40, 460, "release", [("release_id", "uuid", "PK"), ("image_sha", "sha256", ""), ("waves", "jsonb", ""), ("state", "text", "")],
         caption="the rollout controller owns it")
e.entity("wave", 30, 470, 470, "wave", [("release_id", "uuid", "PK"), ("n", "int", "PK"), ("devices", "int", ""), ("verdict", "text", "")], kind="ext",
         caption="soak, compare, continue or halt")
e.entity("rep", 570, 470, 470, "reported_doc", [("device_id", "text", "PK"), ("version", "bigint", ""), ("doc", "jsonb", ""), ("rejected", "jsonb", "")],
         caption="what the device says it runs")
e.entity("tel", 1110, 470, 460, "telemetry (TSDB)", [("cohort, fw, wave", "labels", ""), ("crashes, reconnects", "counters", ""), ("battery", "gauge", "")],
         kind="redis", caption="never labelled by device")
e.rel("des", "dev", "N", "1", src="l:0.5", dst="r:0.5", label="")
e.save(OUT / "erd-physical.svg", order=["dev", "des", "rel", "wave", "rep", "tel"])

# ───────────────────────────── 6 · figures ───────────────────────────────────────────────────────────
def svgdoc(w, h, body): return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                               f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')
def T(x, y, s, size=24, fill=INK, w=500, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{ink(fill)}">{esc(s)}</text>'
def R(x, y, w, h, fill, stroke, rx=10, sw=2.2):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

def tension():
    p = [T(40, 50, "Reach every device, or never break one: a release is both, and you cannot touch the hardware", 28, INK, 800)]
    cards = [("Move fast", "push to everyone at once; one day to 100 %", "a bad image bricks 1 M devices: $150 M", RED, "#fce8e6"),
             ("Move never", "freeze firmware; manual updates", "7 years of unpatched devices", AMBER, "#fef7e0"),
             ("Move in waves", "1,000 first, every hardware rev; halt on signal; devices revert on their own", "blast radius ≤ 100 devices", GREEN, "#e6f4ea")]
    for i, (t, s, n, col, fill) in enumerate(cards):
        x = 60 + i * 510
        p += [R(x, 110, 470, 250, fill, col, rx=14), T(x + 24, 160, t, 27, INK, 800)]
        line, yy = "", 205
        for w_ in s.split():
            if len(line) + len(w_) > 34: p.append(T(x + 24, yy, line, 22, INK, 500)); line, yy = w_, yy + 30
            else: line = (line + " " + w_).strip()
        p += [T(x + 24, yy, line, 22, INK, 500), T(x + 24, 330, n, 22, col, 800)]
    (OUT / "tension.svg").write_text(svgdoc(1600, 400, "".join(p)))
tension()

def waves():
    p = [T(40, 48, "Waves by cohort, each soaked and compared with a control before the next", 28, INK, 800)]
    ws = [("wave 0", "100", "internal devices", 200), ("wave 1", "1,000", "every hardware rev", 260), ("wave 2", "10,000", "+ every region", 470),
          ("wave 3", "100,000", "a person approves", 820), ("wave 4", "rest", "", 1200)]
    x0 = 60
    for i, (n, cnt, note, w) in enumerate(ws):
        x = x0; y = 120 + i * 70
        p += [R(x, y, w, 50, "#e8f0fe" if i < 4 else "#e6f4ea", BLUE if i < 4 else GREEN), T(x + 14, y + 33, f"{n}: {cnt}", 22, INK, 800),
              T(x + max(w, 230) + 16, y + 33, note + ("  ·  soak 24 h, compare" if i < 4 else ""), 21, GREY, 600)]
    p += [R(60, 480, 1480, 60, "#fce8e6", RED), T(80, 518, "Halt rule at every wave: crash rate, reconnects or battery worse than control beyond the interval → stop, revert as v+1", 21, "#c5221f", 700)]
    (OUT / "waves.svg").write_text(svgdoc(1600, 570, "".join(p)))
waves()

bs.budget_bar(OUT / "budget.svg", [("wave 0-1", 2, "edge"), ("wave 2", 2, "service"), ("approval", 1, "data"), ("wave 3", 2, "service"), ("wave 4", 3, "cache")],
              total=14, unit="days", title="A firmware release, from the first device to the last (initial target: 2 weeks)")
print(sorted(pp.name for pp in OUT.glob("*.svg")))
