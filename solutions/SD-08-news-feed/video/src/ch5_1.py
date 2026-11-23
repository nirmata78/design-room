"""5.1 Components and technologies, built from ../stack.json (retrofit shape; SD-96 hand-writes the same slides).
Add `import ch5_1` after ch4_5 in gen.py. IDS = the stack entries to show, in order; DRILL boxes are the entries that carry a `drill`."""
from dsl import *
from stack import *
import json, pathlib
SVG = pathlib.Path(__file__).resolve().parents[1] / "svg"

subchapter("5.1", "Components and technologies", ["C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why."])

for _v in sorted(SVG.glob("c4-containers*-tech.svg")):
    _n = _v.stem
    # no caption: it costs the figure ~60 px of height and the narration says it (layout check, 2026-11-22)
    S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", _n), C4SAY(SVG, _n), cls="dia")

for _id in [s["id"] for s in DATA["stack"]]:
    S(tech(**TECH(_id)), SAY(_id))

S(plain("Technology · the stack on one slide", "The stack, against its rivals",
        table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
        grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), SUMMARY_SAY())

qs("Coach · your turn", "You are the interviewer. Which box would you drill, and what is your one question?", [
 "N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.", "[pause: 3.0]"])

S(plain("Drill · one level down", "The question each box invites",
        table(["Box", "The probe", "A strong answer names"], DRILL(), "bt xs mx") +
        grade("The probe lands on the box you named. The score is set where your answer runs out, so the stack you name is the stack you must defend.")), DRILL_SAY())

def attach_rejl():
    """Add one 'Rejected' line to the first fix slide of every challenge (from stack.json "challenges"); call from gen.py after all chapters."""
    import re
    done = set()
    for s in SL:
        m = re.search(r'Challenge (\d+) of \d+ · the fix<', s["html"])
        if m and m.group(1) not in done and m.group(1) in DATA["challenges"]:
            n = int(m.group(1)); done.add(m.group(1)); tool, why = REJ(n)
            s["html"] += rejl(tool, why)
            t, w = DATA["challenges"][m.group(1)]
            s["say"] = list(s["say"]) + [f"C: Rejected: {say_text(t)}. {say_text(w[0].upper() + w[1:])}"]
