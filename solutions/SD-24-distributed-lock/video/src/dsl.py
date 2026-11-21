"""Tiny DSL: one source of truth for slides and script. Each S() call = one numbered slide + its narration."""
import html as _h
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
    S(body, ["[pause: 1.0]"] + (say if isinstance(say, list) else [say]), cls="th" + (" aux" if aux else ""), name="card " + title)

def subchapter(label, title):
    _cur['n'] = (label, title)

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

def write(outdir):
    import pathlib
    out = pathlib.Path(outdir)
    total = len(SL)
    w = 3 if total >= 100 else 2
    nm = lambda i: f"v-{i:0{w}d}"
    head = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<title>SD-24 distributed lock: slides</title>\n'
            '<link rel="stylesheet" href="style.css">\n<link rel="stylesheet" href="deck.css">\n<link rel="stylesheet" href="video.css">\n'
            '</head><body>\n')
    parts, script = [head], []
    script.append("# SD-24 Distributed lock service: reference solution (Staff L6/L7)\n")
    script.append("<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png, the number printed on every slide.\n"
                  "     Speakers: C candidate · I interviewer · V key line (slower) · N coach. Generated from src/*.py: edit the sources, not this file. -->")
    script.append("<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84 -->")
    script.append("<!-- labels: N=COACH -->")
    script.append("<!-- say: TTL=T-T-L TTLs=T-T-Ls SDK=S-D-K API=A-P-I APIs=A-P-Is SLO=S-L-O SLOs=S-L-Os SLI=S-L-I SLIs=S-L-Is FLP=F-L-P NTP=N-T-P "
                  "SQL=S-Q-L FIFO=fifo GC=G-C gRPC=g-R-P-C CAS=C-A-S RPC=R-P-C fsync=F-sync fsyncs=F-syncs ppm=P-P-M HTTP=H-T-T-P JVM=J-V-M "
                  "ZooKeeper=Zoo-keeper etcd=et-C-D Redis=Reddis ID=I-D IDs=I-Ds EM=E-M AUX=aux SRE=S-R-E RFC=R-F-C CP=C-P DR=D-R UUID=U-U-I-D -->\n")
    last = None
    for i, s in enumerate(SL, 1):
        cls = ("slide " + s["cls"]).strip()
        parts.append(f"<!-- {nm(i)} {e(s['name'] or s['html'][:40])} -->\n<div class=\"{cls}\">\n{s['html']}\n</div>\n")
        if s["chapter"] != last and s["chapter"]:
            n, t = s["chapter"]
            script.append(f"\n## {n} {t}\n"); last = s["chapter"]
        script.append(f"[slide: {nm(i)}]")
        for ln in s["say"]:
            script.append(ln if ln.startswith("[") else ln)
        script.append("")
    parts.append("</body></html>\n")
    (out / "video-slides.html").write_text("".join(parts), encoding="utf-8")
    (out / "distributed-lock-reference.script.md").write_text("\n".join(script), encoding="utf-8")
    return total

def words(prefix):
    import re
    n = 0
    for s in SL:
        for ln in s["say"]:
            if re.match(rf"^{prefix}: ", ln): n += len(ln.split()) - 1
    return n
