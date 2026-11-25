#!/usr/bin/env python3
"""PlantUML → themed SVG + reveal plan, for the video deck and for GitHub Markdown (added 2026-11-25).

One .puml source feeds both outputs: the video inlines the SVG with `<name>.steps.json` (progressive disclosure), the Markdown
booklet embeds the same SVG as `![..](diagrams/name.svg)`, which GitHub renders. C4 diagrams use PlantUML's bundled C4
library (`!include <C4/C4_Container>`, `C4_Component`, `C4_Context`, `C4_Dynamic`): it needs no network.

    from pumlsvg import render
    render('''
    Person(u, "Borrower")
    System_Boundary(b, "Loan platform") {
      Container(api, "Origination API", "Go", "accepts applications")
      ContainerDb(db, "Ledger", "PostgreSQL", "double entry")
    }
    Rel(u, api, "POST /loans", "HTTPS")
    Rel(api, db, "append entries", "SQL")
    ''', "svg/hld-v1.svg", kind="c4", level="container", order=["u", "api", "db"])

kind:   "c4" (container | component | context | dynamic), "seq" (sequence), "state", "erd" (plain `entity`/`class` diagrams), "raw".
        For c4/state/erd the source is the body only; the header (`@startuml`, the include, the Google theme, left-to-right
        layout) is added here. For seq and raw you may pass a full `@startuml … @enduml` text, or just the body.
order:  reveal order for entities (aliases; a tuple reveals several at once). Default: source order. Links appear with the later
        of their two ends. For sequences each message (and note) is one step, in drawing order. Clusters/boundaries stay visible.
Writes: NAME.svg, NAME.steps.json, NAME.meta.json ({"canon", "full"}) — the same sidecars the kit's other generators write.
Errors: PlantUML exits 0 and draws an error image on a syntax error, so the SVG is searched for it and the call raises.
Fonts: C4-PlantUML draws the technology line at a fixed 12 px, below the 18 px 1080p minimum. Leave the `techn` argument EMPTY ("") and
        write the technology into the description / label instead (`Container(api, "Origination API", "", "Go · accepts applications")`,
        `Rel(a, b, "POST /loans [HTTPS]")`); names and descriptions are then 22–24 px. `ev(a, b, "Loan Booked [event]")` is dashed blue, `https(a, b, "POST /loans [HTTPS]")` is solid: write the protocol in the label.
Event versus HTTPS (SD-95 note): use the `ev` / `https` relationship macros defined in the header, so the boundary is drawn:
        `ev(a, b, "Loan Booked [event]")` = dashed blue; `https(a, b, "POST /loans [HTTPS]")` = solid dark.
"""
import json, pathlib, re, subprocess, sys

THEME = r"""
skinparam defaultFontName Inter
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam roundCorner 10
skinparam ArrowColor #202124
skinparam ArrowFontSize 22
skinparam DefaultFontSize 22
skinparam rectangleFontSize 24
skinparam ParticipantBackgroundColor #E8F0FE
skinparam ParticipantBorderColor #4285F4
skinparam ParticipantFontSize 22
skinparam SequenceLifeLineBorderColor #9AA0A6
skinparam SequenceArrowThickness 2
skinparam NoteBackgroundColor #FEF7E0
skinparam NoteBorderColor #FBBC05
skinparam NoteFontSize 18
skinparam StateBackgroundColor #E8F0FE
skinparam StateBorderColor #4285F4
skinparam StateFontSize 22
skinparam StateArrowColor #202124
skinparam EntityBackgroundColor #E8F0FE
skinparam EntityBorderColor #4285F4
skinparam ClassBackgroundColor #E8F0FE
skinparam ClassBorderColor #4285F4
skinparam ClassFontSize 20
"""
C4 = {"container": "C4_Container", "component": "C4_Component", "context": "C4_Context", "dynamic": "C4_Dynamic"}
C4_STYLE = r"""
UpdateElementStyle("person", $bgColor="#1967D2", $fontColor="#FFFFFF", $borderColor="#1967D2")
AddElementTag("store", $bgColor="#188038", $fontColor="#FFFFFF", $borderColor="#188038")
AddElementTag("ext", $bgColor="#9AA0A6", $fontColor="#FFFFFF", $borderColor="#80868B")
AddElementTag("warn", $bgColor="#C5221F", $fontColor="#FFFFFF", $borderColor="#C5221F")
AddRelTag("event", $textColor="#1967D2", $lineColor="#1967D2", $lineStyle=DashedLine())
AddRelTag("https", $textColor="#202124", $lineColor="#202124")
AddRelTag("fail", $textColor="#C5221F", $lineColor="#C5221F", $lineStyle=DashedLine())
!procedure ev($a, $b, $name)
Rel($a, $b, $name, "", $tags="event")
!endprocedure
!procedure https($a, $b, $name)
Rel($a, $b, $name, "", $tags="https")
!endprocedure
"""

def _header(kind, level, direction):
    if kind == "c4":
        lay = {"lr": "LAYOUT_LEFT_RIGHT()", "tb": "LAYOUT_TOP_DOWN()"}[direction]
        return f"@startuml\n!include <C4/{C4[level]}>\n{lay}\nHIDE_STEREOTYPE()\n{THEME}{C4_STYLE}\n"
    pre = "left to right direction\n" if direction == "lr" and kind in ("state", "erd") else ""
    return f"@startuml\n{pre}{THEME}\n"

def run(src, svg_path):
    p = subprocess.run(["plantuml", "-tsvg", "-pipe", "-charset", "UTF-8"], input=src.encode(), capture_output=True)
    svg = p.stdout.decode("utf-8", "replace")
    if p.returncode or "<svg" not in svg or re.search(r"Syntax Error|An error has occured|Cannot find|cannot be parsed|Please use CSS", svg):
        raise SystemExit(f"PlantUML failed for {svg_path}:\n{(p.stderr.decode()[-400:] or re.sub('<[^>]+>', ' ', svg)[:400])}")
    return svg

def _fit(svg):
    """Responsive SVG: keep the viewBox, drop the fixed pixel size and `preserveAspectRatio=none`, so the figure scales to its area."""
    svg = re.sub(r'preserveAspectRatio="none"', 'preserveAspectRatio="xMidYMid meet"', svg)
    svg = re.sub(r'style="width:[\d.]+px;height:[\d.]+px;background:#FFFFFF;"', 'style="background:#FFFFFF;"', svg, count=1)
    return re.sub(r'\s(width|height)="[\d.]+px"', "", svg, count=2)

def _tag(svg, order):
    """Add data-k to the groups that reveal, and return (svg, steps)."""
    keys = []
    if 'data-diagram-type="SEQUENCE"' in svg:
        def msg(m):
            k = f"m:{len(keys)}"; keys.append([k]); return m.group(0).replace("<g ", f'<g data-k="{k}" ', 1)
        svg = re.sub(r'<g class="(?:message|note|divider|reference)"[^>]*>', msg, svg)
        return svg, keys
    ents = re.findall(r'<g class="entity"[^>]*data-qualified-name="([^"]+)"[^>]*id="([^"]+)"', svg)
    alias = {q.split(".")[-1]: i for q, i in ents}; alias.update({i: i for _, i in ents})
    links = [(m.group(1), m.group(2), m.group(3)) for m in re.finditer(
        r'<g class="link"[^>]*data-entity-1="([^"]+)"[^>]*data-entity-2="([^"]+)"[^>]*id="([^"]+)"', svg)]
    seq = [g if isinstance(g, (tuple, list)) else (g,) for g in (order or [q.split(".")[-1] for q, _ in ents])]
    shown, done = set(), set()
    for g in seq:
        ids = [alias[a] for a in g if a in alias]
        shown |= set(ids); step = [f"e:{i}" for i in ids]
        for a, b, lid in links:
            if lid not in done and a in shown and b in shown: done.add(lid); step.append(f"l:{lid}")
        if step: keys.append(step)
    for a, b, lid in links:                                   # links to something not in `order`: with the last step
        if lid not in done and keys: keys[-1].append(f"l:{lid}")
    svg = re.sub(r'<g class="entity"[^>]*id="([^"]+)"', lambda m: m.group(0).replace("<g ", f'<g data-k="e:{m.group(1)}" ', 1), svg)
    svg = re.sub(r'<g class="link"[^>]*id="([^"]+)"', lambda m: m.group(0).replace("<g ", f'<g data-k="l:{m.group(1)}" ', 1), svg)
    return svg, keys

def render(src, out, kind="c4", level="container", direction="lr", order=None, canon=None, full=True, theme=True):
    out = pathlib.Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    body = src.strip()
    if "@startuml" not in body:
        body = _header(kind, level, direction) + body + "\n@enduml\n"
    elif theme and "skinparam defaultFontName" not in body:
        body = body.replace("@startuml", "@startuml\n" + THEME, 1)
    svg = _fit(run(body, out))
    svg, steps = _tag(svg, order)
    out.write_text(svg, encoding="utf-8")
    out.with_suffix(".steps.json").write_text(json.dumps(steps), encoding="utf-8")
    out.with_suffix(".meta.json").write_text(json.dumps({"canon": canon or f"puml:{out.stem}", "full": full}), encoding="utf-8")
    return str(out)

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: raise SystemExit("usage: pumlsvg.py in.puml out.svg [c4|seq|state|erd|raw] [container|component|context|dynamic]")
    print(render(pathlib.Path(a[0]).read_text(), a[1], kind=(a[2] if len(a) > 2 else "raw"), level=(a[3] if len(a) > 3 else "container")))
