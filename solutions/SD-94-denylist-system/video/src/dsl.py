"""Tiny DSL: one source of truth for slides and script. Each S() call = one numbered slide + its narration."""
import html as _h, re
SL = []          # list of dict(kind, html, say, name, chapter)
CH = []          # (index into SL, title) chapter starts
STAGES = ["Requirements", "Estimates", "Theory", "API + data", "Design", "Challenges", "Cost · AUX", "Recap"]
_cur = {"n": None}

def e(s): return _h.escape(s, quote=False)

def S(body, say, cls="", name=""):
    """body: inner html of the slide; say: list of script lines ('C: ...', '[pause: 1.0]', '[reveal: next]')"""
    SL.append(dict(html=body, cls=cls, say=say if isinstance(say, list) else [say], name=name, chapter=_cur["n"]))

def chapter(n, title, stage, sub, say, aux=False):
    """A chapter card: a ribbon slide that also opens the script chapter."""
    _cur["n"] = (n, title)
    ribbon = "".join(f'<span class="{"done" if i < stage else ("on" if i == stage else "")}">{s}</span>' for i, s in enumerate(STAGES))
    body = (f'<div class="lbl">Chapter {n} of 9</div><div class="s">{title}</div><div class="sub">{sub}</div>'
            f'<div class="ribbon">{ribbon}</div>')
    S(body, ([] ) + (say if isinstance(say, list) else [say]), cls="th" + (" aux" if aux else ""), name="card " + title)

def subchapter(label, title, intro=None, sub=""):
    """A sub-section (7.1 ...). Since the 2026-11-17 pacing rework it opens with its own title card and a spoken
    one-sentence introduction, like every chapter."""
    _cur['n'] = (label, title)
    if intro:
        n, _, t = title.partition(": ")
        body = f'<div class="lbl">{label} · {e(n)}</div><div class="s">{e(t or title)}</div>' + (f'<div class="sub">{sub}</div>' if sub else "")
        S(body, intro if isinstance(intro, list) else [intro], cls="th card", name="card " + title)

def fig(name): return f'<figure class="grow"><!--SVG:{name}--></figure>'
def chips(*xs): return '<p class="chips">' + "<i>·</i>".join(xs) + "</p>"
def tr(*pairs): return '<div class="tr">' + "".join(f'<span class="{c}">{e(t)}</span>' for c, t in pairs) + "</div>"
def strip(*cards, cols=""):
    return f'<div class="strip {cols}">' + "".join(f'<div class="{c}"><b class="t">{t}</b>{x}</div>' for c, t, x in cards) + "</div>"
def line(t, cls=""): return f'<div class="line {cls}">{t}</div>'
def grade(t): return f'<div class="grade"><b class="t">Coach · what is graded here</b>{t}</div>'

def dia(kicker, title, svg, extra="", chip=None, trs=None, q=False, red=False, vtag=None):
    h1 = f'<h1 class="q">{title}</h1>' if q else f'<h1>{"<span class=vtag>"+vtag+"</span>" if vtag else ""}{title}</h1>'
    return (f'<div class="k{" r" if red else ""}">{kicker}</div>{h1}' + (chip or "") + (trs or "") + fig(svg) + extra)

def plain(kicker, title, inner, q=False, red=False):
    h1 = f'<h1 class="q">{title}</h1>' if q else f'<h1>{title}</h1>'
    return f'<div class="k{" r" if red else ""}">{kicker}</div>{h1}{inner}'

def table(head, rows, cls="bt sm", ):
    t = f'<table class="{cls}"><tr>' + "".join(f"<th>{h}</th>" for h in head) + "</tr>"
    for r in rows:
        rc = ""
        if isinstance(r, tuple) and len(r) == 2 and isinstance(r[1], list): rc, r = r
        t += f'<tr class="{rc}">' + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return t + "</table>"

def qs(who, q, say):
    S(f'<div class="who">{who}</div><div class="qq">{q}</div><div class="pz">Pause and answer before you continue</div>', say, cls="qs")

def say_slide(text, say):
    S(f'<div class="lbl">If asked, I\'d say</div><div class="s">{text}</div>', say, cls="th say")

def key(lbl, text, say, cls=""):
    S(f'<div class="lbl">{lbl}</div><div class="s">{text}</div>', say, cls="th " + cls)

def trace(kicker, title, lines, hedge=None, red=True):
    body = plain(kicker, title, f'<pre class="trace">{lines}</pre>' + (f'<div class="hedge"><b class="t">Label the numbers</b>{hedge}</div>' if hedge else ""), q=True, red=red)
    return body

# Pacing (ported from theory/video/course.py, 2026-11-17 rework: "too fast, hard to follow the reasoning").
PACE = dict(section_out=1.4, card_in=1.2, card_out=1.8)
PAUSE_AFTER = {"card": 0.0, "th": 1.6, "dia": 1.1, "table": 1.0, "code": 1.0, "tl": 1.0, "qs": 0.6}
PAUSE_BEFORE = {"dia": 1.3, "table": 1.0, "code": 1.0, "tl": 1.0, "th": 0.7}
DEFAULT_AFTER, DEFAULT_BEFORE = 0.8, 0.6

def kind(s):
    c, h = s["cls"].split(), s["html"]
    if s["name"].startswith("card "): return "card"
    if "qs" in c: return "qs"
    if "th" in c: return "th"
    if "<figure" in h: return "dia"
    if "<table" in h and 'class="tl' not in h: return "table"
    if 'class="tl' in h: return "tl"
    if "<pre" in h: return "code"
    return "plain"

_TR = re.compile(r'<pre class="trace">(.*?)</pre>', re.S)
def timeline(m):
    """A monospace trace becomes a two-column timeline table in the body font: no monospace arithmetic or prose."""
    rows = []
    for ln in m.group(1).strip("\n").split("\n"):
        t = re.match(r'\s*<span class="t">(.*?)</span>(.*)$', ln)
        when, what = (t.group(1).strip(), t.group(2).strip()) if t else ("", ln.strip())
        what = what.replace(" × ", " &times; ").replace(" = ", " &#8202;=&#8202; ")
        rows.append(f'<tr><th>{when}</th><td>{what}</td></tr>')
    return '<table class="tl">' + "".join(rows) + "</table>"

def pace(sl):
    """Script lines for every slide, with the beats of the course builder: silence and a card before each section,
    a beat after a slide appears (longer for a figure or table), a beat after it (longer after a key line)."""
    out, prev = [], None
    for i, s in enumerate(sl):
        k = kind(s); say = [x for x in s["say"]]
        lead = [x for x in say[:1] if x.startswith("[pause")]; body = say[len(lead):]
        tail = []
        while body and body[-1].startswith("[pause"): tail.insert(0, body.pop())
        tailv = max([float(re.findall(r"[\d.]+", x)[0]) for x in tail] or [0])
        if k == "card":
            pre = [f"[pause: {PACE['section_out']}]"] if prev is not None else []
            lines = pre, [f"[pause: {PACE['card_in']}]"] + body + [f"[pause: {max(PACE['card_out'], tailv)}]"]
        else:
            lines = [], ([f"[pause: {max(PAUSE_BEFORE.get(k, DEFAULT_BEFORE), float(re.findall(r'[\d.]+', lead[0])[0]) if lead else 0)}]"]
                         + body + [f"[pause: {round(max(PAUSE_AFTER.get(k, DEFAULT_AFTER), tailv), 2)}]"])
        out.append(lines); prev = k
    return out

def write(outdir):
    import pathlib
    out = pathlib.Path(outdir)
    total = len(SL)
    w = 3 if total >= 100 else 2
    nm = lambda i: f"v-{i:0{w}d}"
    head = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<title>SD-94 denylist system: slides</title>\n'
            '<link rel="stylesheet" href="style.css">\n<link rel="stylesheet" href="deck.css">\n<link rel="stylesheet" href="video.css">\n'
            '</head><body>\n')
    parts, script = [head], []
    script.append("# SD-94 Blocking / denylist system: reference solution (Staff L6/L7)\n")
    script.append("<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.\n"
                  "     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->")
    script.append("<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->")
    script.append("<!-- labels: N=COACH -->")
    script.append("<!-- say: denylist=deny-list CIDR=C-I-D-R IPv4=I-P-v-four IPv6=I-P-v-six IP=I-P IPs=I-P-s SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is TTL=T-T-L API=A-P-I APIs=A-P-Is RAM=ram TB=terabytes MB=megabytes GB=gigabytes KB=kilobytes HTTP=H-T-T-P HTTPS=H-T-T-P-S gRPC=g-R-P-C SQL=S-Q-L CDN=C-D-N NAT=nat DDoS=dee-dos TLS=T-L-S ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C DR=D-R UUID=U-U-I-D xDS=x-D-S Redis=Reddis fsync=F-sync ppm=P-P-M JVM=J-V-M LB=load_balancer -->\n")
    last = None
    for s in SL: s["html"] = _TR.sub(timeline, s["html"])
    paced = pace(SL)
    for i, s in enumerate(SL, 1):
        cls = ("slide " + s["cls"]).strip()
        parts.append(f"<!-- {nm(i)} {e(s['name'] or s['html'][:40])} -->\n<div class=\"{cls}\">\n{s['html']}\n</div>\n")
        before, after = paced[i - 1]
        script += before                                   # the silence closing the previous section comes first
        if s["chapter"] != last and s["chapter"]:
            n, t = s["chapter"]
            script.append(f"\n## {n} {t}\n"); last = s["chapter"]
        script.append(f"[slide: {nm(i)}]")
        script += after
        script.append("")
    parts.append("</body></html>\n")
    (out / "video-slides.html").write_text("".join(parts), encoding="utf-8")
    (out / "denylist-reference.script.md").write_text("\n".join(script), encoding="utf-8")
    return total

def words(prefix):
    import re
    n = 0
    for s in SL:
        for ln in s["say"]:
            if re.match(rf"^{prefix}: ", ln): n += len(ln.split()) - 1
    return n
