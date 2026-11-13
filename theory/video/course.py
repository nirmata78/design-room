#!/usr/bin/env python3
"""System-design course builder: one source file per part (src/chNN.txt) → slides + script → frames → MP4 → merged long video.
Ported from the GCP ACE course builder; see README.md for the source format.

  course.py compile [NN…]      src → build/chNN/{video-slides.html,chNN.script.md}, lint, word count
  course.py frames  [NN…]      compile, render 1080p frames, check every slide for overflow
  course.py video   [NN…] [-j3] frames, then MP4s (voice lines cached by content, so an edit re-synthesises only what changed)
  course.py merge              out/SD-Part-*.mp4 → out/SD-Full-Course.mp4 (stream copy, chapters combined)
  course.py coverage           every concept in concepts.tsv has exactly one home slide, in its assigned part
  course.py index              writes INDEX.md: concept → part → section (→ timestamp once the part's MP4 exists)
  course.py companion [NN…]    companion/SD-Building-Blocks-Companion.md: reading plan, then per part the readings, concepts with
                               their lines to say, figures, traps and probe drills, all extracted from the sources
  course.py stats              words, slides, questions, estimated and real durations
Heavy output lives in ~/.cache/sd-course/ and ~/Movies/SD-Building-Blocks-course/, outside the repository."""
import html, json, pathlib, re, subprocess, sys, concurrent.futures as cf

TOOL = pathlib.Path(__file__).resolve().parent
# --root DIR builds another deck with the same tool (a task's episode series): DIR holds src/, svg/ and series.json
# {"name": "SD-20", "footer": "Distributed cache", "unit": "Episode", "title": "...", "out": "~/Movies/...", "teacher": "COACH"}.
ROOT = pathlib.Path(sys.argv[sys.argv.index("--root") + 1]).resolve() if "--root" in sys.argv else TOOL
if "--root" in sys.argv:
    i = sys.argv.index("--root"); del sys.argv[i:i + 2]
CFG = json.loads((ROOT / "series.json").read_text()) if (ROOT / "series.json").exists() else {}
NAME, UNIT = CFG.get("name", "SD"), CFG.get("unit", "Part")
HERE = ROOT
SRC, SVG, SHOTS = HERE / "src", HERE / "svg", HERE / "shots"
BUILD = pathlib.Path.home() / ".cache/sd-course/build" / (NAME if CFG else "")
OUT = pathlib.Path(CFG.get("out", "~/Movies/SD-Building-Blocks-course")).expanduser()
KIT = pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"
PDFPY = pathlib.Path.home() / "Projects/design-room/pdf-kit/.venv/bin/python"
TTSPY = pathlib.Path.home() / ".cache/kokoro-tts/.venv/bin/python"

# Five voices (2026-11-12): N narrator · V key line (slower) · I interviewer · C candidate · E aside (traps, "then and now", stories)
HEAD = """<!-- voices: N=af_heart@0.92 I=bf_emma@0.95 C=am_michael@0.9 V=af_bella@0.86 E=af_sarah@0.94 -->
<!-- labels: N=@TEACHER@ I=INTERVIEWER C=CANDIDATE V=SAY_THIS E=ASIDE -->
"""
SPEECH = re.compile(r"^([NVICE]): (.+)$")
SENT = "\x01"          # marks a body line that appears only after the [reveal] cue
ASIDE_PANELS = ("trap", "watch", "now", "new")
SENTENCES = re.compile(r"(?<=[.?!])\s+")
BADSPOKEN = re.compile(r"[→·≥≤~&%`*_=<>\[\]{}|]|--")

def inline(s):
    codes = []
    def stash(m):
        codes.append(f"<code>{html.escape(m.group(1))}</code>"); return f"\0{len(codes)-1}\0"
    s = re.sub(r"`([^`]+)`", stash, s)
    s = html.escape(s, quote=False).replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>").replace("&lt;br&gt;", "<br>")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"==(.+?)==", r"<mark>\1</mark>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return re.sub(r"\0(\d+)\0", lambda m: codes[int(m.group(1))], s)

def plain(s):
    return re.sub(r"\*\*|==|`|(?<![\w*])\*(?=\S)|(?<=\S)\*(?![\w*])", "", s)

def cells(line):
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]

def un(b):
    """(line without the staging mark, is it revealed later?)"""
    return b.lstrip(SENT), b.startswith(SENT)

def takeaways(body):
    keep, lines = [], []
    for b in body:
        b2, h = un(b)
        m = re.match(r"^>([!~]?) (.+)$", b2)
        if m:
            lines.append(f'<div class="line{ {"!":" r","~":" a"}.get(m.group(1),"") }{" rv" if h else ""}">{inline(m.group(2))}</div>')
        else:
            keep.append(b)
    return keep, "".join(lines)

class Chapter:
    def __init__(self, nn):
        self.nn, self.n = nn, int(nn)
        self.slides, self.script, self.lint, self.questions = [], [], [], []
        self.short, self.section, self.title = "", "", ""
        self.pending_q = None
        self.concepts, self.missing = [], []
        self.staged, self.b_idx = False, 0

    def head(self, flags):
        return " ".join(f for f in flags if f in ("new",))

    def _add(self, cls, inner, cue):
        self.slides.append(f'<div class="slide {cls}">{inner}'
                           f'<div class="foot"><span>{html.escape(CFG.get("footer", "System design"))} · {UNIT} {self.n} · {html.escape(self.short)}</span>'
                           f'<span>{html.escape(self.section)}</span></div></div>')
        if cue: self.script.append(f"\n[slide: @@{len(self.slides)}@@]")
        return len(self.slides)

    def slide(self, cls, inner):
        """A staged slide is two frames of one numbered slide: A hides the later parts, B (an extra, unnumbered frame) shows all.
        The script shows A, and a [reveal] cue crossfades to B."""
        if self.staged:
            self._add(cls + " stageA", inner, True)
            self.b_idx = self._add(cls + " stageB extra", inner, False)
        else:
            self._add(cls, inner, True)

    def chapter_card(self, title):
        """A title card for every '## n.m Title' section: shown on its own for one second, then the first slide of the section."""
        m = re.match(r"^(\d+\.\d+)\s+(.*)$", title)
        num, name = m.groups() if m else ("", title)
        self.script.append(f"\n## {title}")
        self.slides.append(f'<div class="slide ch-title extra"><div class="ct-ep">{UNIT} {self.n} · {html.escape(self.title)}</div>'
                           f'<div class="ct-num">{html.escape(num)}</div><div class="ct-t">{inline(name)}</div></div>')
        self.script += [f"[slide: @@{len(self.slides)}@@]", "[pause: 1.0]"]

    def top(self, k, t, red=False):
        return f'<div class="k{" r" if red else ""}">{inline(k)}</div><h1>{inline(t)}</h1>' if t else f'<div class="k{" r" if red else ""}">{inline(k)}</div>'

    def emit(self, typ, flags, fields, body):
        new = " ".join(f for f in ("new", "aux") if f in flags)
        red = "r" in flags
        k = fields[0] if fields else ""; t = fields[1] if len(fields) > 1 else ""
        self.staged = any(b.startswith(SENT) for b in body)
        body, lines = takeaways(body)
        if typ == "th":
            sub = f'<div class="sub">{inline(fields[2])}</div>' if len(fields) > 2 and fields[2] else ""
            self.slide(f"th {new}", f'<div class="lbl">{inline(k)}</div><div class="s">{inline(t)}</div>{sub}')
        elif typ in ("table", "cmd"):
            hid = [un(b)[1] for b in body]
            rows = [cells(un(b)[0]) for b in body]
            if len(rows) > 8: self.lint.append(f"{t!r}: {len(rows)} rows")
            head = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
            def td(c): return f"<td>{c.strip('`') and html.escape(c.strip('`'))}</td>"
            rv = lambda i: ' class="rv"' if hid[i] else ""
            if typ == "cmd":
                tr = "".join(f"<tr{rv(i)}><td>{inline(r[0])}</td>{td(r[1])}</tr>" for i, r in enumerate(rows) if i)
            else:
                tr = "".join(f"<tr{rv(i)}>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for i, r in enumerate(rows) if i)
            cls = "bt" + (" sm" if "sm" in flags else "") + (" cmd" if typ == "cmd" else "")
            self.slide(new, self.top(k, t, red) + f'<table class="{cls}"><tr>{head}</tr>{tr}</table>{lines}')
        elif typ == "cards":
            n = next((f for f in flags if re.fullmatch(r"c\d", f)), f"c{min(len(body),4)}")
            cs = ""
            for b in body:
                b, h = un(b)
                m = re.match(r"^(?:(red|grn|amb) )?(.+?) :: (.+)$", b)
                if not m: sys.exit(f"bad card: {b}")
                cs += f'<div class="cd {m.group(1) or ""}{" rv" if h else ""}"><h3>{inline(m.group(2))}</h3><p>{inline(m.group(3))}</p></div>'
            self.slide(new, self.top(k, t, red) + f'<div class="cards {n}">{cs}</div>{lines}')
        elif typ == "tiles":
            ts = "".join((lambda c, h: f'<div class="tile{" rv" if h else ""}"><b>{inline(c[0])}</b><span>{inline(c[1])}</span></div>')(cells(un(b)[0]), un(b)[1]) for b in body)
            self.slide(new, self.top(k, t, red) + f'<div class="tiles" style="--n:{len(body)}">{ts}</div>{lines}')
        elif typ == "list":
            lead = "".join(f'<p class="lead{" rv" if un(b)[1] else ""}">{inline(un(b)[0][2:])}</p>' for b in body if un(b)[0].startswith("~ "))
            its = "".join(f'<li{" class=rv" if un(b)[1] else ""}>{inline(un(b)[0][2:])}</li>' for b in body if un(b)[0].startswith("- "))
            self.slide(new, self.top(k, t, red) + lead + f'<ul class="big">{its}</ul>{lines}')
        elif typ == "dia":
            name = un(body[0])[0].strip()
            if not (SVG / f"{name}.svg").exists(): self.missing.append(name)
            self.slide("dia " + new, self.top(k, t, red) + f'<figure class="grow"><!--SVG:{name}--></figure>{lines}')
        elif typ == "shot":
            # A Cloud Console screenshot from shots/ (gitignored, local only): first body line is the file name,
            # an optional "~ caption" line sits under the picture.
            name = body[0].strip(); cap = "".join(f'<figcaption>{inline(b[2:])}</figcaption>' for b in body[1:] if b.startswith("~ "))
            if not (SHOTS / name).exists(): self.lint.append(f"missing screenshot {name}")
            self.slide("dia shot " + new, self.top(k, t, red) + f'<figure class="grow shot"><img src="{(SHOTS / name).as_uri()}" alt=""></figure>{cap}{lines}')
        elif typ == "code":
            self.slide(new, self.top(k, t, red) + f'<pre class="code">{html.escape(chr(10).join(body))}</pre>{lines}')
        elif typ == "panel":
            kind = next((f for f in flags if f in ("trap", "watch", "tip", "key", "new", "note", "now")), "key")
            label = {"trap": "Trap", "watch": "Easy to confuse", "tip": "How to spot it", "key": "Remember", "new": "New in the June 2026 guide", "note": "Worth knowing", "now": "Then and now"}[kind]
            ps = "".join(f'<p{" class=rv" if un(b)[1] else ""}>{inline(un(b)[0])}</p>' for b in body)
            self.slide(new, self.top(k, t, kind == "trap") + f'<div class="panel {kind}"><div class="pl">{label}</div>{ps}</div>{lines}')
        else:
            sys.exit(f"unknown slide type {typ}")

    def question(self, flags, fields, body):
        stem = fields[0]
        opts = {m.group(1): m.group(2) for m in (re.match(r"^\(([A-F])\) (.+)$", b) for b in body) if m}
        ans = next(b[4:].replace(" ", "").split(",") for b in body if b.startswith("ans "))
        why = {m.group(1): m.group(2) for m in (re.match(r"^why ([A-F]) :: (.+)$", b) for b in body) if m}
        qn = len(self.questions) + 1
        multi = len(ans) > 1
        if set(opts) - set(why): self.lint.append(f"Q{qn}: no reason for {set(opts) - set(why)}")
        if set(ans) - set(opts): self.lint.append(f"Q{qn}: answer not among options")
        kind = "Choose " + {2: "two", 3: "three"}[len(ans)] if multi else "Choose one"
        who = f"Part {self.n} · sample question {qn} · {kind}"
        ops = "".join(f'<div class="opt"><b class="l">{l}</b><span>{inline(x)}</span></div>' for l, x in opts.items())
        self.slide("qz", f'<div class="who">{who}</div><div class="stem">{inline(stem)}</div>{ops}'
                         f'<div class="hint">Pause and decide. Name the phrase in the stem that decides it.</div>')
        read = plain(stem) + " " + " ".join(f"{l}. {plain(x).rstrip('.')}." for l, x in opts.items())
        self.script.append("I: " + read)
        pause = 9 if multi else 7
        self.script.append(f"[pause: {pause}]")
        rev = "".join(f'<div class="opt {"ok" if l in ans else "no"}"><b class="l">{l}</b>{inline(x)}'
                      f'<span class="why">{"Correct. " if l in ans else ""}{inline(why.get(l, ""))}</span></div>' for l, x in opts.items())
        self.slide("qz rev", f'<div class="who">Question {qn} · answer {", ".join(ans)}</div><div class="stem">{inline(stem)}</div>{rev}')
        self.questions.append((stem, opts, ans, why))

    def prep(self, typ, body, speech):
        """Staging: '+++' in a body hides everything below it until the [reveal] cue in the narration. With neither, a slide that
        has a takeaway bar and at least three spoken sentences gets the bar revealed on its last sentence."""
        if "+++" in body:
            i = body.index("+++")
            body = body[:i] + [SENT + b for b in body[i + 1:]]
            if "[reveal]" not in speech: self.lint.append(f"{typ} slide has +++ but no [reveal] line")
            return body, speech
        voiced = [k for k, s in enumerate(speech) if isinstance(s, tuple) and s[0] in "NE"]
        has_bar = any(re.match(r"^>[!~]? ", b) for b in body)
        if typ in ("th", "code", "q") or not has_bar or not voiced or "[reveal]" in speech: return body, speech
        if sum(len(SENTENCES.split(speech[k][1])) for k in voiced) < 3: return body, speech
        k = voiced[-1]; sents = SENTENCES.split(speech[k][1])
        speech = list(speech)
        if len(sents) >= 2:
            speech[k:k + 1] = [(speech[k][0], " ".join(sents[:-1])), "[reveal]", (speech[k][0], sents[-1])]
        elif len(voiced) >= 2:
            speech.insert(k, "[reveal]")
        else:
            return body, speech
        return [SENT + b if re.match(r"^>[!~]? ", b) else b for b in body], speech

    def flush_slide(self, cur):
        typ, flags, fields, body, speech = cur
        aside = typ == "panel" and any(f in ASIDE_PANELS for f in flags)
        if typ == "q":
            self.question(flags, fields, body)
        elif typ == "probe":
            self.probe_slide(fields, body)
        else:
            body, speech = self.prep(typ, body, speech)
            self.emit(typ, flags, fields, body)
        self.staged = False
        for s in speech:
            if isinstance(s, tuple):
                code, text = s
                if code == "N" and (aside or re.match(r"^(A story|Here are three stories)", text)): code = "E"
                self.script.append(f"{code}: {text}")
            elif s == "[reveal]":
                self.script.append(f"[reveal: @@{self.b_idx}@@]")
            else:
                self.script.append(s)

    def parse(self, text):
        cur = None
        def flush():
            nonlocal cur
            if cur: self.flush_slide(cur); cur = None
        for raw in text.splitlines():
            line = raw.rstrip()
            if line.startswith("#!"):
                m = re.match(r"#!\s*(\w+):\s*(.+)", line); setattr(self, m.group(1), m.group(2)); continue
            if cur and cur[0] == "code" and not SPEECH.match(line) and not line.startswith(("= ", "## ", "[pause", "[reveal", "@ ")):
                cur[3].append(line); continue
            if not line.strip(): continue
            if line.startswith("## "):
                flush(); self.section = line[3:]; self.chapter_card(line[3:]); continue
            if line.startswith("= "):
                flush()
                parts = cells(line[2:]); head = parts[0].split()
                cur = [head[0], head[1:], parts[1:], [], []]; continue
            if line.startswith("@ "):
                self.concepts += [(i, self.section) for i in line[2:].split()]; continue
            m = SPEECH.match(line)
            if m or line.startswith("[pause") or line.strip() == "[reveal]":
                if m:
                    if BADSPOKEN.search(m.group(2)): self.lint.append("symbol in speech: " + m.group(2)[:70])
                    if len(m.group(2).split()) > 110: self.lint.append("long line: " + m.group(2)[:50])
                item = (m.group(1), m.group(2)) if m else line.strip()
                (cur[4] if cur else self.script).append(item if cur else line)
                continue
            if cur: cur[3].append(line.strip()); continue
            sys.exit(f"ch{self.nn}: stray line: {line[:80]}")
        flush()

    def probe_slide(self, fields, body):
        """One numbered slide: the question first, and after a pause the strong answer fades in under it (frame B of the same slide)."""
        q = fields[0]
        if BADSPOKEN.search(plain(q)): self.lint.append("symbol in probe: " + q[:70])
        body = [SENT + b for b in body]
        self.staged = True
        body, lines = takeaways(body)
        its = "".join(f"<li class=rv>{inline(un(b)[0][2:])}</li>" for b in body if un(b)[0].startswith("- "))
        self.slide("qz pr", f'<div class="who">{UNIT} {self.n} · interviewer probe</div><div class="stem">{inline(q)}</div>'
                            f'<div class="pa"><div class="hintA">Pause and answer aloud. Then compare.</div>'
                            f'<div class="alab rv">A strong answer</div><ul class="big rv">{its}</ul>{lines}</div>')
        self.staged = False
        self.script.append("I: " + plain(q)); self.script.append("[pause: 3.0]"); self.script.append(f"[reveal: @@{self.b_idx}@@]")

    def write(self):
        d = BUILD / f"ch{self.nn}"; d.mkdir(parents=True, exist_ok=True)
        pad = len(str(len(self.slides)))
        style = f'<style>.slide::after {{ content: "{self.n}." counter(sl); }}</style>'
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>System design course</title>'
                '<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="deck.css">'
                f'<link rel="stylesheet" href="video.css"><link rel="stylesheet" href="sd.css">{style}</head><body>\n'
                + "\n".join(self.slides) + "\n</body></html>\n")
        (d / "video-slides.html").write_text(page, encoding="utf-8")
        sc = "\n".join(self.script)
        sc = re.sub(r"@@(\d+)@@", lambda m: "v-" + m.group(1).zfill(pad), sc)
        (d / f"ch{self.nn}.script.md").write_text(f"# {CFG.get('title', 'System design course')}, {UNIT.lower()} {self.n}: {self.title}\n{HEAD.replace('@TEACHER@', CFG.get('teacher', 'TEACHER'))}\n{sc}\n", encoding="utf-8")
        words = sum(len(s.split()) - 1 for s in self.script if SPEECH.match(s))
        return dict(nn=self.nn, title=self.title, slides=len(self.slides), words=words, q=len(self.questions))

def source(nn):
    """A part is src/chNN.txt, or a folder src/chNN/ of segment files joined in name order (small pieces first, merged here)."""
    f, d = SRC / f"ch{nn}.txt", SRC / f"ch{nn}"
    return f.read_text(encoding="utf-8") if f.exists() else "\n".join(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.txt")))

def chapters(args):
    want = [a.zfill(2) for a in args if a.isdigit()]
    have = sorted({p.stem[2:] for p in SRC.glob("ch*.txt")} | {p.name[2:] for p in SRC.glob("ch*") if p.is_dir()})
    return [n for n in have if not want or n in want]

def compile_ch(nn):
    c = Chapter(nn); c.parse(source(nn))
    info = c.write()
    for l in c.lint: print(f"  ch{nn} lint: {l}")
    if c.missing: print(f"  ch{nn}: {len(c.missing)} diagrams not drawn yet: {' '.join(sorted(set(c.missing)))}")
    pauses = sum(float(x) for x in re.findall(r"\[pause: ([\d.]+)\]", "\n".join(c.script)))
    info["est_min"] = round((info["words"] * 0.43 + pauses * 0.6) / 60, 1)
    print(f"ch{nn}: {info['slides']} slides, {info['words']} words, {info['q']} questions, ~{info['est_min']} min — {info['title']}")
    return c, info

def frames_ch(nn):
    d = BUILD / f"ch{nn}"; f = d / "frames"
    if f.exists():
        for p in f.glob("*.png"): p.unlink()
    subprocess.run([str(PDFPY), str(TOOL / "render_check.py"), str(d / "video-slides.html"), str(TOOL), str(f), str(SVG)], check=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = d / "video-slides.review.pdf"      # one page per numbered slide: no title cards, the complete (revealed) version of each
    if pdf.exists(): (OUT / f"{NAME}-{UNIT}-{nn}-slides.pdf").write_bytes(pdf.read_bytes())

def video_ch(nn):
    d = BUILD / f"ch{nn}"; OUT.mkdir(parents=True, exist_ok=True)
    c = Chapter(nn); c.parse(source(nn))
    slug = re.sub(r"[^A-Za-z0-9]+", "-", c.title).strip("-")
    out = OUT / f"{NAME}-{UNIT}-{nn}-{slug}.mp4"
    log = d / "build.log"
    with log.open("w") as lf:
        subprocess.run([str(TTSPY), str(TOOL / "build_cached.py"), str(d / f"ch{nn}.script.md"), "--frames", str(d / "frames"), "--out", str(out), "--dissolve", "0.3", "--chapter-gap", "0"],
                       check=True, stdout=lf, stderr=subprocess.STDOUT)
    print(log.read_text().splitlines()[-1] if False else f"built {out.name}", flush=True)

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_chapters", "-show_streams", "-show_format", "-of", "json", str(p)], check=True, capture_output=True, text=True)
    return json.loads(r.stdout)

def clock(s):
    s = int(s); h, m, s = s // 3600, s // 60 % 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def merge():
    parts = sorted(OUT.glob(f"{NAME}-{UNIT}-*.mp4"))
    if not parts: sys.exit("no parts")
    sig = None; meta = [";FFMETADATA1", "title=" + CFG.get("title", "System design: theory and building blocks")]; t = 0.0; rows = []
    lst = OUT / ".concat.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    for p in parts:
        d = probe(p)
        s = tuple((x["codec_type"], x["codec_name"], x.get("width"), x.get("height"), x.get("r_frame_rate"), x.get("sample_rate"), x.get("channels"), x.get("pix_fmt"), x.get("profile"))
                  for x in d["streams"] if x["codec_type"] in ("video", "audio"))
        if sig and s != sig: sys.exit(f"{p.name}: stream parameters differ, cannot stream-copy: {s} vs {sig}")
        sig = s
        for c in d["chapters"]:
            a, b = float(c["start_time"]) + t, float(c["end_time"]) + t
            meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(a*1000)}", f"END={int(b*1000)}", "title=" + c["tags"]["title"]]
            rows.append((a, c["tags"]["title"]))
        t += float(d["format"]["duration"])
    mf = OUT / ".chapters.txt"; mf.write_text("\n".join(meta) + "\n", encoding="utf-8")
    out = OUT / (f"{NAME}-Full.mp4" if CFG else "SD-Full-Course.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(mf), "-map", "0", "-map_metadata", "1", "-map_chapters", "1",
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    (OUT / "chapters.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    real = float(probe(out)["format"]["duration"])
    print(f"{out}: {clock(real)} (sum of parts {clock(t)}), {len(rows)} chapters, {out.stat().st_size/1e9:.2f} GB")

def register():
    rows = [l.split("\t") for l in (HERE / "concepts.tsv").read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
    return {r[0]: dict(name=r[1], tier=r[2], part=int(r[3]), form=r[4]) for r in rows}

def homes(nns):
    out = {}
    for nn in nns:
        c = Chapter(nn); c.parse(source(nn))
        for cid, sec in c.concepts: out.setdefault(cid, []).append((int(nn), sec))
    return out

def coverage(nns):
    reg, got, bad = register(), homes(nns), []
    built = {int(n) for n in nns}
    for cid, r in reg.items():
        if r["part"] not in built: continue
        h = got.get(cid, [])
        if not h: bad.append(f"{cid} ({r['name']}): no home slide in part {r['part']}")
        elif len(h) > 1: bad.append(f"{cid}: declared {len(h)} times: {h}")
        elif h[0][0] != r["part"]: bad.append(f"{cid}: home is part {r['part']}, declared in part {h[0][0]}")
    bad += [f"{cid}: not in concepts.tsv (dropped or mistyped)" for cid in got if cid not in reg]
    n = sum(1 for r in reg.values() if r["part"] in built)
    print(f"coverage: {n - sum(1 for b in bad if 'no home' in b)} of {n} concepts homed in parts {sorted(built)}; {len(bad)} problems")
    for b in bad: print("  " + b)
    return not bad

def index(nns):
    reg, got = register(), homes(nns)
    stamps = {}
    for p in OUT.glob(f"{NAME}-{UNIT}-*.mp4"):
        n = int(p.name.split("-")[2])
        for c in probe(p)["chapters"]: stamps[(n, c["tags"]["title"])] = clock(float(c["start_time"]))
    rows = ["# Course index", "", "Generated by `course.py index`. One row per concept: where the course teaches it.",
            "Task videos cite these rows instead of teaching the concept again.", "",
            "| Concept | Name | Tier | Part | Section | At |", "|---|---|---|---|---|---|"]
    for cid, r in reg.items():
        h = got.get(cid)
        sec = h[0][1] if h else "(not written yet)"
        rows.append(f"| {cid} | {r['name']} | {r['tier']} | {r['part']} | {sec} | {stamps.get((r['part'], sec), '')} |")
    (HERE / "INDEX.md").write_text("\n".join(rows) + "\n", encoding="utf-8"); print(f"INDEX.md: {len(reg)} rows")

def records(nn):
    """The source of a part as plain records, for extraction (no rendering): one dict per slide, in order."""
    out, cur, sec, title = [], None, "", ""
    for raw in source(nn).splitlines():
        line = raw.rstrip()
        if line.startswith("#! title:"): title = line.split(":", 1)[1].strip(); continue
        if line.startswith("#!"): continue
        if cur and cur["type"] == "code" and not SPEECH.match(line) and not line.startswith(("= ", "## ", "[pause", "[reveal", "@ ")):
            cur["body"].append(line); continue
        if not line.strip() or line.startswith(("[pause", "[reveal")): continue
        if line.startswith("## "): sec = line[3:]; cur = None; continue
        if line.startswith("= "):
            parts = cells(line[2:]); head = parts[0].split()
            cur = dict(type=head[0], flags=head[1:], fields=parts[1:], body=[], speech=[], ids=[], section=sec); out.append(cur); continue
        if line.startswith("@ "):
            if cur: cur["ids"] += line[2:].split()
            continue
        m = SPEECH.match(line)
        if m:
            if cur: cur["speech"].append((m.group(1), m.group(2)))
            continue
        if cur: cur["body"].append(line.strip())
    return title, out

def reading_plan():
    """§2.3 of plan 02, the reading table, printed as it stands."""
    p = HERE.parent.parent / "plans/02-concepts-and-building-blocks-course.md"
    if not p.exists(): return []
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^### 2\.3 · [^\n]*\n(.*?)(?=^Each part's brief)", t, re.S | re.M)
    return [m.group(1).strip()] if m else []

def md(s):
    """Source inline marks → pandoc Markdown (they are already Markdown, except ==mark== and <br>)."""
    s = re.sub(r"==(.+?)==", r"**\1**", s).replace("<br>", " ").replace("|", "\\|").replace("≈", r"$\approx$")
    sup = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
    return re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: "^" + m.group(0).translate(sup) + "^", s)

def companion(nns, out=None):
    """companion/SD-Building-Blocks-Companion.md: pure extraction from the sources, no new prose."""
    reg = register()
    doc = ["---", "title: System design · building blocks and concepts", "subtitle: Written companion to the 17-part course", "fontsize: 10pt",
           "geometry: a4paper,top=0.7in,bottom=0.75in,left=0.75in,right=0.75in",
           "---", "", "# The reading plan", ""] + reading_plan() + [""]
    counts = {}
    for nn in nns:
        title, recs = records(nn)
        n = int(nn); doc += [f"# Part {n} · {md(title)}", ""]
        def panel(name):
            return [md(b) for r in recs if r["type"] == "panel" and r["fields"] and r["fields"][0] == name for b in r["body"]]
        for lab, name in (("Assumed reading", "Assumed reading"), ("Read next", "Read next")):
            ps = panel(name)
            if ps: doc += [f"**{lab}.**", ""] + [f"- {p}" for p in ps] + [""]
        # the concept's key line: the V: line on a th slide whose kicker starts with the concept's ID
        lines = {}
        for r in recs:
            if r["type"] == "th" and r["fields"]:
                vid = r["fields"][0].split(" ")[0]
                v = next((s for c, s in r["speech"] if c == "V"), None)
                if v and vid not in lines: lines[vid] = v
        homed = [(i, r["section"]) for r in recs for i in r["ids"]]
        doc += ["## Concepts", "", "| ID | Name | Tier | The line to say | Section |", "|" + "|".join("-" * n for n in (8, 18, 4, 56, 14)) + "|"]
        for cid, sec in homed:
            g = reg.get(cid, {})
            doc.append(f"| {cid} | {md(g.get('name', ''))} | {g.get('tier', '')} | {md(lines.get(cid, ''))} | {md(sec)} |")
        doc.append("")
        figs = [r for r in recs if r["type"] == "dia"]
        if figs:
            doc += ["## Figures", ""]
            for r in figs:
                name = r["body"][0].strip(); cap = md(r["fields"][1] if len(r["fields"]) > 1 else r["fields"][0])
                doc += [f"![{cap}](diagrams/video-{name}.pdf){{width=100%}}", ""]
        traps = [r for r in recs if r["type"] == "panel" and any(f in ("trap", "watch") for f in r["flags"])]
        if traps:
            doc += ["## Traps and easy confusions", ""]
            for r in traps:
                kind = "Trap" if "trap" in r["flags"] else "Easy to confuse"
                head = md(r["fields"][1] if len(r["fields"]) > 1 else r["fields"][0])
                doc += [f"**{kind} · {head}.** " + " ".join(md(b) for b in r["body"] if not b.startswith(">")), ""]
        probes = [r for r in recs if r["type"] == "probe"]
        if probes:
            doc += ["## Probe drills", ""]
            for k, r in enumerate(probes, 1):
                doc += [f"**{k}. {md(r['fields'][0])}**", ""]
                doc += [f"- {md(b[2:])}" for b in r["body"] if b.startswith("- ")]
                doc += [f"- *{md(b[2:])}*" for b in r["body"] if b.startswith("> ")]
                doc += [""] + [f"> {s}" for c, s in r["speech"] if c == "C"] + [""]
        counts[nn] = dict(concepts=len(homed), figures=len(figs), probes=len(probes))
    path = out or (HERE / "companion" / "SD-Building-Blocks-Companion.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(doc) + "\n", encoding="utf-8")
    for nn, c in counts.items(): print(f"part {int(nn)}: {c['concepts']} concepts, {c['figures']} figures, {c['probes']} probes")
    return counts

def main():
    cmd = sys.argv[1]; args = sys.argv[2:]
    jobs = next((int(a[2:]) for a in args if a.startswith("-j")), 3)
    nns = chapters(args)
    if cmd in ("compile", "frames", "video", "stats"):
        infos = [compile_ch(n)[1] for n in nns]
        if len(infos) > 1:
            print(f"TOTAL {sum(i['slides'] for i in infos)} slides, {sum(i['words'] for i in infos)} words, {sum(i['q'] for i in infos)} questions, ~{sum(i['est_min'] for i in infos)/60:.1f} h")
    if cmd in ("frames", "video"):
        with cf.ThreadPoolExecutor(4) as ex: list(ex.map(frames_ch, nns))
    if cmd == "video":
        with cf.ThreadPoolExecutor(jobs) as ex: list(ex.map(video_ch, nns))
    if cmd == "merge":
        merge()
    if cmd == "coverage":
        sys.exit(0 if coverage(nns) else 1)
    if cmd == "index":
        index(nns)
    if cmd == "companion":
        companion(nns)
    if cmd == "stats":
        for p in sorted(OUT.glob("*.mp4")):
            d = probe(p); print(f"{p.name}: {clock(float(d['format']['duration']))}, {len(d['chapters'])} chapters, {p.stat().st_size/1e6:.0f} MB")

if __name__ == "__main__":
    main()
