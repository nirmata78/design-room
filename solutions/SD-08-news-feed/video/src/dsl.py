"""One source of truth for slides and script. Each S() call = one logical slide + its narration.

Progressive disclosure (2026-11-21): a logical slide is shown as several frames, one per reveal step, so the viewer sees a
table filled row by row and a diagram drawn box by box in request-flow order, as a candidate would at a whiteboard.

Reveal units, in document order, are found automatically at write time:
  - every body row of a table (the header stays), every row of a trace timeline;
  - every card, tile, property block, case / fix / why / hedge strip, takeaway line, grading note and interviewer answer;
  - every unit of an inlined figure: <!--SVG:name--> reads svg/name.steps.json, written by the kit's generators
    (boxes and arrows in request-flow order, one message per unit for a sequence).
The narration places them: "[+]" reveals the next unit, "[+N]" the next N, "[+*]" all that remain. Lines before the first
marker are spoken over the slide with nothing revealed. A slide that has units must reveal all of them (checked), unless it is
made with steps=False (then it is shown whole: thesis cards, "if asked" slides).

REVEAL_REPORT=1 python3 gen.py  does not stop at the first slide whose markers do not match its units: it lists every one, with
the source file and line, the unit count and the reveal count, and writes nothing. Used to retrofit older solutions (RETROFIT.md).
"""
import html as _h, json, os, pathlib, re, sys

SL = []          # list of dict(kind, html, say, name, chapter, steps)
STAGES = ["Requirements", "Estimates", "Theory", "API + data", "Design", "Challenges", "Cost · AUX", "Recap"]
META = dict(title="SD-NN: slides", heading="# SD-NN: reference solution", stem="reference", svg=None,
            voices="N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=am_michael@0.84", names="C=Candidate V=Candidate N=Coach I=Interviewer",
            say="", automark=False)
_cur = {"n": None}

def e(s): return _h.escape(s, quote=False)

def _where():
    f = sys._getframe(1)
    while f and f.f_code.co_filename == __file__: f = f.f_back
    return f"{pathlib.Path(f.f_code.co_filename).name}:{f.f_lineno}" if f else "?"

def S(body, say, cls="", name="", steps=True):
    """body: inner html of the slide; say: list of script lines ('C: ...', '[pause: 1.0]', '[+]')."""
    SL.append(dict(html=body, cls=cls, say=say if isinstance(say, list) else [say], name=name, chapter=_cur["n"], steps=steps,
                   src=_where()))

def chapter(n, title, stage, sub, say, aux=False):
    """A chapter card: a ribbon slide that also opens the script chapter."""
    _cur["n"] = (n, title)
    ribbon = "".join(f'<span class="{"done" if i < stage else ("on" if i == stage else "")}">{s}</span>' for i, s in enumerate(STAGES))
    body = (f'<div class="lbl">Chapter {n} of 9</div><div class="s">{title}</div><div class="sub">{sub}</div>'
            f'<div class="ribbon">{ribbon}</div>')
    S(body, say if isinstance(say, list) else [say], cls="th" + (" aux" if aux else ""), name="card " + title, steps=False)

def subchapter(label, title, intro=None, sub=""):
    """A sub-section (5.1, 7.1 ...) with its own title card and a spoken one-sentence introduction."""
    _cur['n'] = (label, title)
    if intro:
        n, _, t = title.partition(": ")
        body = f'<div class="lbl">{label} · {e(n)}</div><div class="s">{e(t or title)}</div>' + (f'<div class="sub">{sub}</div>' if sub else "")
        S(body, intro if isinstance(intro, list) else [intro], cls="th card", name="card " + title, steps=False)

def fig(name, cap=None):
    c = f'<figcaption>{cap}</figcaption>' if cap else ""
    return f'<figure class="grow" data-f="{name}"><!--SVG:{name}-->{c}</figure>'
def chips(*xs): return '<p class="chips">' + "<i>·</i>".join(xs) + "</p>"
def tr(*pairs): return '<div class="tr">' + "".join(f'<span class="{c}">{e(t)}</span>' for c, t in pairs) + "</div>"
def strip(*cards, cols=""):
    return f'<div class="strip {cols}">' + "".join(f'<div class="{c}"><b class="t">{t}</b>{x}</div>' for c, t, x in cards) + "</div>"
def line(t, cls=""): return f'<div class="line {cls}">{t}</div>'
def rejl(tool, why):
    """One line under a fix: the tool an interviewer will name, and the property that rules it out (one reveal unit)."""
    return f'<div class="rejb"><b class="t">Rejected</b><b>{tool}</b>: {why}</div>'
def grade(t): return f'<div class="grade"><b class="t">Coach · what is graded here</b>{t}</div>'
def cards(*cs, cols=2):
    """cards(("grn", "Title", "text"), ...): a grid of cards, each one reveal unit."""
    return f'<div class="cards c{cols}">' + "".join(f'<div class="cd {c}"><h3>{t}</h3><p>{x}</p></div>' for c, t, x in cs) + "</div>"

def dia(kicker, title, svg, extra="", chip=None, trs=None, q=False, red=False, vtag=None, cap=None):
    h1 = f'<h1 class="q">{title}</h1>' if q else f'<h1>{"<span class=vtag>"+vtag+"</span>" if vtag else ""}{title}</h1>'
    return (f'<div class="k{" r" if red else ""}">{kicker}</div>{h1}' + (chip or "") + (trs or "") + fig(svg, cap) + extra)

def plain(kicker, title, inner, q=False, red=False):
    h1 = f'<h1 class="q">{title}</h1>' if q else f'<h1>{title}</h1>'
    return f'<div class="k{" r" if red else ""}">{kicker}</div>{h1}{inner}'

def table(head, rows, cls="bt sm"):
    t = f'<table class="{cls}"><tr>' + "".join(f"<th>{h}</th>" for h in head) + "</tr>"
    for r in rows:
        rc = ""
        if isinstance(r, tuple) and len(r) == 2 and isinstance(r[1], list): rc, r = r
        t += f'<tr class="{rc}">' + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return t + "</table>"

def qs(who, q, say):
    S(f'<div class="who">{who}</div><div class="qq">{q}</div><div class="pz">Pause and answer before you continue</div>', say, cls="qs", steps=False)

def say_slide(text, say):
    S(f'<div class="lbl">If asked, I\'d say</div><div class="s">{text}</div>', say, cls="th say", steps=False)

def key(lbl, text, say, cls=""):
    S(f'<div class="lbl">{lbl}</div><div class="s">{text}</div>', say, cls="th " + cls, steps=False)

def trace(kicker, title, events, hedge=None, red=True):
    """events: [(time, html)]; one timeline row per event, revealed one at a time."""
    rows = "".join(f'<tr><th>{t}</th><td>{x}</td></tr>' for t, x in events)
    return plain(kicker, title, f'<table class="tl">{rows}</table>' +
                 (f'<div class="hedge"><b class="t">{hedge[0]}</b>{hedge[1]}</div>' if hedge else ""), q=True, red=red)

def tech(kicker, title, pick, how, rejected, cite=None, cls=""):
    """A technology slide: the pick and how it is built one level deep, then each rejected alternative and why."""
    rows = [("pick", [f"<b>{pick[0]}</b>", pick[1]])] + [("rej", [f"{n}", w]) for n, w in rejected]
    inner = (f'<div class="techhow"><b class="t">How it is built</b>{how}</div>' +
             table(["Option", "Why it is chosen, or why not"], rows, "bt xs mx tech") +
             (f'<div class="cite">Background: {cite}</div>' if cite else ""))
    return plain(kicker, title, inner)

# ── older-format traces: <pre class="trace"> → a timeline table (kept for retrofitted solutions; new slides use trace()) ──
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

# ── pacing (ported from theory/video/course.py, 2026-11-17 rework) ──
PACE = dict(section_out=1.4, card_in=1.2, card_out=1.8)
PAUSE_AFTER = {"card": 0.0, "th": 1.6, "dia": 1.1, "table": 1.0, "code": 1.0, "tl": 1.0, "qs": 0.6}
PAUSE_BEFORE = {"dia": 1.3, "table": 1.0, "code": 1.0, "tl": 1.0, "th": 0.7}
DEFAULT_AFTER, DEFAULT_BEFORE = 0.8, 0.6
MAX_STEPS = 12            # a slide with more reveal steps is two slides (GUIDELINES §7.2)
REVEAL_BEAT = 0.45        # after a reveal, a beat so the eye lands on the new element before the voice explains it

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

# ── reveal units ──
UNIT_DIV = re.compile(r'<div class="(?:cd|tile|prop|case|fixb|whyb|rejb|hedge|line|grade|ans|techhow)\b')
TOKENS = re.compile(r'<table[^>]*>|</table>|<tr\b|' + UNIT_DIV.pattern + r'|<!--SVG:([\w.-]+)-->')

def tag_units(h, svgdir):
    """Insert data-u="k" on every html unit; return (html, units). A unit is ("u", k) or ("svg", figure, [keys])."""
    out, units, pos, tables = [], [], 0, []
    for m in TOKENS.finditer(h):
        out.append(h[pos:m.start()]); tok = m.group(0); pos = m.end()
        if tok.startswith("<table"):
            tables.append(dict(tl='class="tl' in tok, row=0)); out.append(tok)
        elif tok == "</table>":
            tables and tables.pop(); out.append(tok)
        elif tok == "<tr":
            t = tables[-1] if tables else dict(tl=True, row=1)
            t["row"] += 1
            if t["tl"] or t["row"] > 1:
                units.append(("u", len(units))); out.append(f'<tr data-u="{len(units)-1}"')
            else:
                out.append(tok)
        elif tok.startswith("<!--SVG:"):
            name = m.group(1); out.append(tok)
            p = svgdir / f"{name}.steps.json"
            if p.exists():
                for keys in json.loads(p.read_text()):
                    units.append(("svg", name, keys))
        else:
            units.append(("u", len(units))); out.append(tok.replace("<div ", f'<div data-u="{len(units)-1}" ', 1))
    out.append(h[pos:])
    return "".join(out), units

MARK = re.compile(r"^\[\+(\d+|\*)?\]$")

def pages(s, units):
    """Split a slide's narration at the reveal markers: [(visible_unit_count, lines)]."""
    out, vis, cur = [], 0, []
    for ln in s["say"]:
        m = MARK.match(ln)
        if not m:
            cur.append(ln); continue
        if not s["steps"]:
            raise SystemExit(f"slide {s['name'] or s['html'][:50]!r}: reveal marker on a steps=False slide")
        if cur or out:
            out.append((vis, cur)); cur = []
        n = m.group(1)
        vis = len(units) if n == "*" else vis + int(n or 1)
        if vis > len(units):
            raise SystemExit(f"slide {s['name'] or s['html'][:60]!r}: {vis} reveals but only {len(units)} units")
    out.append((vis, cur))
    if s["steps"] and units and vis < len(units):
        raise SystemExit(f"slide {s['name'] or re.sub('<[^>]+>', ' ', s['html'])[:70]!r}: only {vis} of {len(units)} units revealed "
                         f"(figure plans: {sorted({u[1] for u in units if u[0] == 'svg'})}); add [+] markers or steps=False")
    if not s["steps"]:
        out = [(len(units), out[0][1])]
    return out

def hide_css(pid, units, vis, fresh):
    sel, now = [], []
    for i, u in enumerate(units):
        if u[0] == "u":
            k = f'#{pid} [data-u="{u[1]}"]'
            (sel if i >= vis else now if i >= fresh else []).append(k)
        else:
            for key in u[2]:
                k = f'#{pid} figure[data-f="{u[1]}"] [data-k="{key}"]'
                if i >= vis: sel.append(k)
    css = (",".join(sel) + "{visibility:hidden}") if sel else ""
    css += "".join(f"{k.replace(' [', ' tr[')} > td{{background:var(--now)}}" for k in now)   # only rows match: a soft tint on the row just added
    return f"<style>{css}</style>" if css else ""

def pace(k, prev, say_first, say_last):
    """Lead and tail pauses of one logical slide (the course builder's beats)."""
    lead = [x for x in say_first[:1] if x.startswith("[pause")]
    tail = [x for x in say_last[::-1] if x.startswith("[pause")][:1]
    tailv = float(re.findall(r"[\d.]+", tail[0])[0]) if tail else 0
    if k == "card":
        return ([f"[pause: {PACE['section_out']}]"] if prev is not None else []), [f"[pause: {PACE['card_in']}]"], [f"[pause: {max(PACE['card_out'], tailv)}]"]
    leadv = float(re.findall(r"[\d.]+", lead[0])[0]) if lead else 0
    return [], [f"[pause: {max(PAUSE_BEFORE.get(k, DEFAULT_BEFORE), leadv)}]"], [f"[pause: {round(max(PAUSE_AFTER.get(k, DEFAULT_AFTER), tailv), 2)}]"]

def strip_edge_pauses(lines, first, last):
    if first:
        while lines and lines[0].startswith("[pause"): lines = lines[1:]
    if last:
        while lines and lines[-1].startswith("[pause"): lines = lines[:-1]
    return lines


# ── legacy narration: place reveal markers automatically (retrofit aid, 2026-11-22) ──
# A slide whose narration has no (or too few) markers is not an error when META["automark"] is on: its spoken lines are split into
# sentences (then clauses, when sentences are fewer than units) and dealt out to the reveal units in order, using word overlap between
# each unit's text and each sentence to choose the cut points. Slides written for the current standard carry hand-placed markers and
# are never touched. Hand-place markers wherever the result reads badly; the report names what was automarked.
AUTOMARKED = []
_SENT = re.compile(r'(?<=[.?!])\s+(?=[A-Z“"\'(0-9])')
_CLAUSE = re.compile(r'(?<=[,;:])\s+(?=\w)|\s+(?:—|and then|but|so|while)\s+')
_W = lambda t: {w for w in re.findall(r"[a-z0-9]{4,}", t.lower())}

def _unit_texts(h, units):
    ks = [(m.start(), int(m.group(1))) for m in re.finditer(r'data-u="(\d+)"', h)]
    txt = {}
    for i, (pos, k) in enumerate(ks):
        end = ks[i + 1][0] if i + 1 < len(ks) else len(h)
        txt[k] = re.sub(r"<[^>]+>", " ", h[pos:end])
    return [txt.get(i, "") for i in range(len(units))]

def automark(s, h, units):
    U = len(units)
    items = []                                   # (is_sentence, text)
    for ln in s["say"]:
        m = re.match(r"^([A-Z]): (.*)$", ln, re.S)
        if not m or MARK.match(ln): items.append((False, ln)); continue
        for sen in _SENT.split(m.group(2).strip()): items.append((True, f"{m.group(1)}: {sen}"))
    def count(): return sum(1 for a, _ in items if a)
    if count() < U:                               # not enough sentences: cut at clauses, longest first
        while count() < U:
            cand = [(i, len(t.split())) for i, (a, t) in enumerate(items) if a and len(_CLAUSE.split(t[3:])) > 1]
            if not cand: break
            i = max(cand, key=lambda c: c[1])[0]; v = items[i][1][:3]; parts = _CLAUSE.split(items[i][1][3:], maxsplit=1)
            items[i:i+1] = [(True, v + parts[0].strip()), (True, v + parts[1].strip())]
    sidx = [i for i, (a, _) in enumerate(items) if a]; M = len(sidx)
    if M == 0: return False
    G = min(U, M)                                 # groups of consecutive sentences, one per marker
    ut = _unit_texts(h, units); uw = [_W(t) for t in ut]
    # unit counts per group (when sentences < units, some groups reveal several units)
    per = [U // G + (1 if g < U % G else 0) for g in range(G)]
    first = [sum(per[:g]) for g in range(G)]      # first unit of each group
    sw = [_W(items[i][1]) for i in sidx]
    # dynamic programme: cut[g] = first sentence of group g; maximise overlap of the group's first unit with its sentences, even-ish sizes
    import functools
    ideal = M / G
    @functools.lru_cache(None)
    def best(g, start):
        if g == G: return (0.0, ()) if start == M else (-1e9, ())
        out = (-1e9, ())
        for end in range(start + 1, M - (G - g - 1) + 1):
            words = set().union(*sw[start:end]); ref = uw[first[g]] if uw[first[g]] else set()
            sc = len(ref & words) / (len(ref) + 2) - 0.12 * abs((end - start) - ideal)
            rest = best(g + 1, end)
            if rest[0] + sc > out[0]: out = (rest[0] + sc, (start,) + rest[1])
        return out
    cuts = best(0, 0)[1]
    if not cuts: cuts = tuple(round(g * ideal) for g in range(G))
    mark_at = {sidx[c]: per[g] for g, c in enumerate(cuts)}
    new = []
    for i, (a, t) in enumerate(items):
        if i in mark_at: new.append("[+]" if mark_at[i] == 1 else f"[+{mark_at[i]}]")
        new.append(t)
    s["say"] = new
    return True

def report(svgdir):
    """REVEAL_REPORT mode: every slide whose markers do not cover its units, with where to edit it."""
    bad = []
    for s in SL:
        h, units = tag_units(s["html"], svgdir)
        if not s["steps"] or not units and not any(MARK.match(x) for x in s["say"]): continue
        try: pages(s, units)
        except SystemExit:
            marks = [MARK.match(x).group(1) for x in s["say"] if MARK.match(x)]
            n = sum(len(units) if m == "*" else int(m or 1) for m in marks)
            spoken = sum(1 for x in s["say"] if re.match(r"^[A-Z]: ", x))
            figs = sorted({u[1] for u in units if u[0] == "svg"})
            bad.append(f"{s['src']:<16} units {len(units):>3}  reveals {n:>3}  spoken lines {spoken:>3}  "
                       f"{(s['name'] or re.sub('<[^>]+>', ' ', s['html']))[:60].strip()!r}" + (f"  figures {figs}" if figs else ""))
    print("\n".join(bad) or "all slides reveal all their units")
    print(f"{len(bad)} of {len(SL)} slides need markers (or steps=False)")
    raise SystemExit(0)

def write(outdir):
    out = pathlib.Path(outdir); svgdir = pathlib.Path(META["svg"] or out / "svg")
    for s in SL: s["html"] = _TR.sub(timeline, s["html"])
    if os.environ.get("REVEAL_REPORT"):
        report(svgdir)
    plan = []
    for s in SL:
        h, units = tag_units(s["html"], svgdir)
        if not s["steps"]:
            units = []          # shown whole; any data-u stays inert
        elif units and META.get("automark"):
            try: pages(s, units)
            except SystemExit:
                s["say"] = [x for x in s["say"] if not MARK.match(x)]
                if automark(s, h, units): AUTOMARKED.append(s["src"])
        plan.append((s, h, units, pages(s, units)))
    total = sum(len(pg) for _, _, _, pg in plan)
    big = [(s["src"], len(pg)) for s, _, _, pg in plan if len(pg) > MAX_STEPS]
    if big:
        print(f"warning: {len(big)} slides have more than {MAX_STEPS} reveal steps (split them): {big[:6]}")
    w = max(2, len(str(total)))
    nm = lambda i: f"v-{i:0{w}d}"
    head = (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<title>{e(META["title"])}</title>\n'
            '<link rel="stylesheet" href="style.css">\n<link rel="stylesheet" href="deck.css">\n<link rel="stylesheet" href="video.css">\n<link rel="stylesheet" href="google-theme.css">\n'
            '</head><body>\n')
    parts, script = [head], [META["heading"] + "\n"]
    script.append("<!-- Video script for slide-video-kit/scripts/build_video.py. [slide: v-NNN] = frames/v-NNN.png; [reveal: v-NNN] = the next\n"
                  "     reveal step of the same slide. Generated from src/*.py: edit the sources, not this file. -->")
    script.append(f"<!-- voices: {META['voices']} -->")
    script.append(f"<!-- names: {META['names']} -->")
    if META["say"]:
        script.append(f"<!-- say: {META['say']} -->")
    script.append("")
    last, prev, page = None, None, 0
    for n, (s, h, units, pg) in enumerate(plan, 1):
        k = kind(s)
        before, lead, tail = pace(k, prev, s["say"], s["say"])
        script += before
        if s["chapter"] != last and s["chapter"]:
            c, t = s["chapter"]
            script.append(f"\n## {c} {t}\n"); last = s["chapter"]
        fresh = 0
        for j, (vis, lines) in enumerate(pg):
            page += 1; pid = f"p{page}"
            cls = ("slide " + s["cls"]).strip()
            parts.append(f"<!-- {nm(page)} · slide {n}{f' step {j+1}/{len(pg)}' if len(pg) > 1 else ''} · {e(s['name'] or re.sub('<[^>]+>', ' ', s['html'])[:40])} -->\n"
                         f'<div class="{cls}" id="{pid}" data-n="{n}">{hide_css(pid, units, vis, fresh if j else vis)}\n{h}\n</div>\n')
            fresh = vis
            body = strip_edge_pauses(list(lines), j == 0, j == len(pg) - 1)
            if j == 0:
                script.append(f"[slide: {nm(page)}]"); script += lead
            else:
                script.append(f"[reveal: {nm(page)}]"); script.append(f"[pause: {REVEAL_BEAT}]")
            script += body
        script += tail; script.append("")
        prev = k
    parts.append("</body></html>\n")
    (out / "video-slides.html").write_text("".join(parts), encoding="utf-8")
    (out / f"{META['stem']}.script.md").write_text("\n".join(script), encoding="utf-8")
    if AUTOMARKED: print(f"automarked {len(AUTOMARKED)} legacy slides (hand-place markers to refine): {AUTOMARKED[:6]} …")
    return len(SL), total

def words(prefix):
    n = 0
    for s in SL:
        for ln in s["say"]:
            if re.match(rf"^{prefix}: ", ln): n += len(ln.split()) - 1
    return n

def words_by_chapter():
    out = {}
    for s in SL:
        c = s["chapter"][0] if s["chapter"] else "-"
        c = str(c).split(".")[0]
        out[c] = out.get(c, 0) + sum(len(ln.split()) - 1 for ln in s["say"] if re.match(r"^[A-Z]: ", ln))
    return out

# ── LaTeX and highlighted code (the course builder's KaTeX and highlight.js helpers, cached on disk) ──
import json as _json, pathlib as _pl, subprocess as _sp
_TV = _pl.Path(__file__).resolve().parents[4] / "theory" / "video"
_CACHE = _pl.Path.home() / ".cache/sd-course"
def _node(script, cachefile, key, payload):
    f = _CACHE / cachefile
    d = _json.loads(f.read_text()) if f.exists() else {}
    if key not in d:
        r = _sp.run(["node", str(_TV / script)], input=_json.dumps([payload]), capture_output=True, text=True)
        if r.returncode: raise SystemExit(f"{script} failed: {r.stderr[-300:]}")
        d[key] = _json.loads(r.stdout)[0]; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(_json.dumps(d))
    return d[key]

def tex(src):
    """A display formula as MathML."""
    m = _node("tex.js", "tex.json", f"1|{src}", [src, True]).replace(' display="block"', "")
    return f'<div class="fxone">{m}</div>'

# Code on a 1080p slide (2026-11-22): pseudocode by default; a real language only when its idiom is the lesson (the exact
# client call, the conditional write). Short lines, few of them, and the lines the narration is about marked as key lines.
CODE_COLS, CODE_LINES = 56, 12
_LANGS = {"python": "python", "sql": "sql", "http": "http", "json": "json", "go": "go", "java": "java", "rust": "rust",
          "ts": "typescript", "typescript": "typescript", "bash": "bash", "yaml": "yaml"}
_PSEUDO_KW = re.compile(r"\b(if|then|else|elif|for|each|in|while|until|repeat|return|function|def|try|catch|retry|and|or|not|"
                        r"do|end|on|wait|emit|with|loop|break|continue|let|var)\b")

def _pseudo_hl(src):
    """A tiny highlighter for pseudocode: keywords, strings, numbers and comments (# or //)."""
    out = []
    for ln in src.split("\n"):
        body, _, cm = ln.partition("#") if "#" in ln else ln.partition("//")
        mark = "#" if "#" in ln else "//"
        b = e(body)
        b = re.sub(r"(&quot;[^&]*&quot;|\"[^\"]*\"|'[^']*')", r'<span class="hljs-string">\1</span>', b)
        b = re.sub(r"(?<![\w.])(\d[\d_,.]*)(?![\w])", r'<span class="hljs-number">\1</span>', b)
        b = _PSEUDO_KW.sub(r'<span class="hljs-keyword">\1</span>', b)
        out.append(b + (f'<span class="hljs-comment">{mark}{e(cm)}</span>' if cm or ln.rstrip().endswith(mark) else ""))
    return "\n".join(out)

def _split_lines(h):
    """Split highlighted HTML into lines, closing and reopening spans that cross a line break."""
    lines, stack, cur = [], [], ""
    for tok in re.split(r"(<span[^>]*>|</span>|\n)", h):
        if tok == "\n":
            lines.append(cur + "</span>" * len(stack)); cur = "".join(stack)
        elif tok.startswith("<span"):
            stack.append(tok); cur += tok
        elif tok == "</span>":
            stack and stack.pop(); cur += tok
        else:
            cur += tok
    return lines + [cur + "</span>" * len(stack)]

def code(src, lang="pseudo", hl=(), cols=None):
    """Code on a slide, highlighted with the Google-theme token colours (video.css), its language shown as the flag.
    lang: "pseudo" (default; the rule is pseudocode unless the idiom is the point) or go, python, sql, http, json, java …
    hl:   1-based line numbers of the key lines (tinted and barred): the lines the narration is about.
    Refuses a line longer than CODE_COLS (56) characters or more than CODE_LINES (12) lines: shorten it or split the slide."""
    src = src.strip("\n"); lines = src.split("\n"); cols = cols or CODE_COLS
    long = [l for l in lines if len(l) > cols]
    if long or len(lines) > CODE_LINES:
        raise SystemExit(f"{_where()}: code block too wide or too long for 1080p ({len(lines)} lines, max {CODE_LINES}; "
                         f"longest {max(map(len, lines))} characters, max {cols}): {(long or lines)[0].strip()[:50]!r}")
    if lang == "pseudo":
        h = _pseudo_hl(src)
    else:
        h = _node("hl.js", "hl.json", f"{_LANGS[lang]}|{src}", [src, _LANGS[lang]])
    keys = set(hl)
    body = "".join(f'<span class="ln{" key" if i in keys else ""}">{l or " "}</span>' for i, l in enumerate(_split_lines(h), 1))
    flag = "pseudocode" if lang == "pseudo" else lang
    return f'<pre class="code hl{" keys" if keys else ""}" data-lang="{flag}">{body}</pre>'

def pseudo(src, hl=()):
    """Pseudocode (the default for code on a slide)."""
    return code(src, "pseudo", hl)
