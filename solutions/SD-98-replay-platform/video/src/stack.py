"""The technology choices, from one file: <solution>/stack.json.

Used three ways, so the video, the booklet and the outline cannot drift apart:
  - by the slide sources:  from stack import TECH, SUMMARY, DRILL, REJ, C4  (see ch4_5.py and the challenge chapters);
  - by diagrams.py:        stack.C4 gives the type and description lines of the container view with technologies;
  - from the shell:        python3 video/src/stack.py sync   rewrites the marked regions of the booklet and OUTLINE.md:
        <!-- stack:sections -->  …  <!-- /stack:sections -->   (booklet Stage 5: one section per technology)
        <!-- stack:summary -->   …  <!-- /stack:summary -->    (booklet: the stack table and the fix-slide rejections)
        <!-- stack:outline -->   …  <!-- /stack:outline -->    (OUTLINE.md: the 5.1 table)
     The text between the markers is generated; edit stack.json, never the region.
Text in stack.json is Markdown-lite: `code` and **bold**. html() turns it into slide HTML, md() leaves it for pandoc.
Kit template: ~/.claude/skills/slide-video-kit/templates/reference-solution/stack.py (copy, do not import).
"""
import html as _h, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]          # the solution folder
DATA = json.loads((ROOT / "stack.json").read_text(encoding="utf-8"))
STACK = {s["id"]: s for s in DATA["stack"]}
C4 = {k: tuple(v) for k, v in DATA.get("c4", {}).items()}

def html(s):
    s = _h.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)

def md(s): return s

def plain_text(s): return re.sub(r"[`*]", "", s)

# ── slide helpers (dsl.tech / dsl.table take HTML) ──
def TECH(id_):
    """Arguments for dsl.tech(): kicker, title, (pick, why), how, [(name, why)], cite."""
    s = STACK[id_]
    return dict(kicker=s["kicker"], title=html(s["title"]), pick=(html(s["pick"]), html(s["why"])), how=html(s["how"]),
                rejected=[(html(n), html(w)) for n, w in s["rejected"]], cite=s.get("course"))

def SUMMARY():
    """Rows of the stack table: Container · Choice · Rejected · The deciding reason."""
    return [[html(c) for c in s["summary"]] for s in DATA["stack"] if s.get("summary")]

def DRILL():
    """Rows of the drill interlude: [box, probe, what a strong answer names (the short form)]."""
    return [[html(s["summary"][0] if s.get("summary") else s["heading"].split(":")[0]), html(s["drill"][0]), html(s["drill"][2])]
            for s in DATA["stack"] if s.get("drill")]

def REJ(n):
    """(tool, why) rejected on challenge n's fix slide."""
    t, w = DATA["challenges"][str(n)]
    return html(t), html(w)


# ── narration built from the same file (a retrofit aid: new solutions may hand-write it, as SD-96 does) ──
def say_text(s):
    s = re.sub(r"[`*]", "", s)
    for a, b in (("→", " to "), ("≈", "about "), ("×", " times "), ("≥", " at least "), ("≤", " at most "), (" / ", " or "), ("&", " and ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()

def SAY(id_, P="[+]"):
    """Narration for dsl.tech(): how it is built, why, then each rejected alternative; one reveal marker per table row."""
    s = STACK[id_]; t = say_text
    out = [P, "C: " + t(s["how"]), P, f"C: Why {t(s['pick'])}: " + t(s["why"])]
    for i, (n, w) in enumerate(s["rejected"]):
        out += [P, f"C: {'Rejected: ' if i == 0 else ''}{t(n)}. " + t(w)]
    return out

def SUMMARY_SAY(P="[+]"):
    out = ["C: The stack on one slide, as I would leave it on the whiteboard."]
    for s in DATA["stack"]:
        if s.get("summary"):
            c, ch, rej, why = (say_text(x) for x in s["summary"])
            out += [P, f"C: {c}: {ch}. Not {rej}. {why[0].upper() + why[1:]}."]
    return out + ["N: Naming a product is not the signal. Naming the property that rules out its rival is. Interviewers go one level down on whichever box you name, so name only what you can defend."]

def DRILL_SAY(P="[+]"):
    out = ["N: Here is where interviewers usually go."]
    for s in DATA["stack"]:
        if s.get("drill"):
            out += [P, "I: " + say_text(s["drill"][0]), "[pause: 1.2]", "N: " + say_text(s["drill"][1])]
    return out + ["N: If you picked a box that is not on this list, good. Write its probe down and answer it before you watch on."]

def C4SAY(svgdir, name="c4-containers-tech", P="[+]"):
    """One sentence per reveal unit of the container view: the node's title and its technology."""
    units = json.loads((pathlib.Path(svgdir) / f"{name}.steps.json").read_text())
    out = ["C: The container view again, with one change: the type line now names the technology. I will walk it once, then defend each choice on its own slide."]
    for keys in units:
        nodes = [k[2:] for k in keys if k.startswith("n:") and k[2:] in C4]
        t = say_text("; ".join(f"{C4[n][0]} is {C4[n][1]}" for n in nodes)) if nodes else "The path between them."
        out += [P, "C: " + t + "."]
    return out

# ── Markdown for the booklet and the outline ──
def md_sections():
    out = []
    for s in DATA["stack"]:
        out += [f"## {s['heading']}", ""]
        how = s["how"] + (" " + s["detail"] if s.get("detail") else "")
        out += [f"*How it is built.* {how}", "", f"*Why {s['pick']}:* {s['why']}", "", "*Rejected:*", ""]
        out += [f"- **{plain_text(n)}**: {w}" for n, w in s["rejected"]]
        out += ["", f"*Course:* {s['course']}."]
        if s.get("drill"):
            out += ["", f"*Drill.* \"{s['drill'][0]}\" {s['drill'][1]}"]
        if s.get("figure"):
            out += ["", s["figure"]]
        out.append("")
    return "\n".join(out).rstrip() + "\n"

def md_summary():
    rows = [s["summary"] for s in DATA["stack"] if s.get("summary")]
    t = ["| Container | Choice | Rejected | The deciding reason |", "|---|---|---|---|"]
    t += [f"| {' | '.join(r)} |" for r in rows]
    t += ["", "Each fix in Stage 6 rejects one tool by name:", "", "| Deep dive | Rejected | Because |", "|---|---|---|"]
    t += [f"| 6.{n} | {tool} | {why} |" for n, (tool, why) in sorted(DATA["challenges"].items(), key=lambda kv: int(kv[0]))]
    return "\n".join(t) + "\n"

def md_outline():
    t = ["| Container | Choice | How it is built | Rejected | Theory part |", "|---|---|---|---|---|"]
    for s in DATA["stack"]:
        rej = "; ".join(plain_text(n) for n, _ in s["rejected"])
        t.append(f"| {s['heading'].split(':')[0]} | {s['pick']} | {s['how'].split('. ')[0]} | {rej} | {s['parts']} |")
    t += ["", "Fix-slide rejections: " + "; ".join(f"{n}: {plain_text(tool)}" for n, (tool, _) in
                                                     sorted(DATA["challenges"].items(), key=lambda kv: int(kv[0]))) + "."]
    return "\n".join(t) + "\n"

def _replace(path, tag, body):
    txt = path.read_text(encoding="utf-8")
    pat = re.compile(rf"(<!-- stack:{tag} -->\n).*?(<!-- /stack:{tag} -->)", re.S)
    if not pat.search(txt):
        sys.exit(f"{path.name}: no <!-- stack:{tag} --> … <!-- /stack:{tag} --> region")
    new = pat.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(2), txt)
    if new != txt:
        path.write_text(new, encoding="utf-8")
    return new != txt

def sync():
    booklet = next(ROOT.glob("SD-*_Reference_Design.md"))
    changed = [_replace(booklet, "sections", md_sections()), _replace(booklet, "summary", md_summary()),
               _replace(ROOT / "video" / "OUTLINE.md", "outline", md_outline())]
    print("stack sync:", "updated" if any(changed) else "up to date")

if __name__ == "__main__":
    if sys.argv[1:] != ["sync"]:
        sys.exit("usage: stack.py sync")
    sync()
