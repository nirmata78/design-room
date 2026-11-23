"""5.1 Components and technologies, built from ../stack.json (retrofit shape; SD-96 hand-writes the same slides).
Add `import ch5_1` after ch4_5 in gen.py. IDS = the stack entries to show, in order; DRILL boxes are the entries that carry a `drill`."""
from dsl import *
from stack import *
import json, pathlib
SVG = pathlib.Path(__file__).resolve().parents[1] / "svg"

subchapter("5.1", "Components and technologies", ["C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech",
      cap="The container view with technologies; every choice has a rejected alternative on a later slide"), C4SAY(SVG), cls="dia")

S(dia("Architecture · C4 components · decision orchestrator", "Inside the box that owns time", "c4-comp-orch",
      cap="C4 level 3: the components challenges 1, 2 and 8 open"), [
 "C: One level further down, inside the box the challenges will drill most: the decision orchestrator.",
 "[+]", "C: The application service asks for a decision.",
 "[+]", "C: The gather owns one two-second deadline for every call, a Go error group under a context deadline.",
 "[+]", "C: First, the tier-zero checks, in process and free: eligibility, the blocklist and velocity, our own loan book.",
 "[+]", "C: Then the vendor adapters, one per vendor, called at once. Each holds a circuit breaker and a token bucket at the contract rate.",
 "[+]", "C: They call the bureau, identity and fraud vendors over mutual TLS.",
 "[+]", "C: At the deadline, the policy client sends the features and the list of what is missing,",
 "[+]", "C: and the policy engine scores it.",
 "[+]", "C: The record writer writes one record per decision,",
 "[+]", "C: into the decision records store, write once.",
 "[+]", "C: And the late-answer recorder keeps whatever arrives after two seconds, because it was paid for."], cls="dia")

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

# ───────── 5.2 · the alternate path (GUIDELINES §3.2) ─────────
subchapter("5.2", "When you don't need all this", ["C: Before I break it, the simpler design. Not every lender needs a second bureau and a signed missing-data table, and saying where the line is counts as judgement."])

S(dia("Alternate path · one box changes", "One bureau, and refer whatever is missing", "alt",
      extra=strip(("case", "What it gives up", "About 3 % of applications are referred, and about one in five of those walks away. No small-known-customer row, no second bureau."),
                  ("whyb", "The crossover", "Lost loans ≈ A × 3 % × 20 % × 42 % × $70 ≈ $0.18 × A a month, against ≈ $60k a month for a second bureau: A ≈ 330,000 applications."))), [
 "C: The alternate path changes one box. The orchestrator, the deadline and the state machine stay.",
 "[+]", "C: The credit vendors box, marked alternate, becomes one bureau, and the policy has one rule for anything missing at the deadline: refer.",
 "[+]", "C: What it gives up, precisely: about three percent of applications are referred, and about one in five of those customers walks away before the text arrives. There is no small-known-customer row and no second bureau to fall back on.",
 "[+]", "C: The crossover, from the scale line. Lost loans cost about A times three percent, times one in five walking away, times forty-two percent who would have taken a loan, times about seventy dollars of margin: eighteen cents an application a month. A second bureau costs about sixty thousand dollars a month in minimums and integration. The two meet at about three hundred and thirty thousand applications a month. Illustrative numbers."], cls="dia")

say_slide("“Below about three hundred thousand applications a month I would ship one bureau and refer. At two million, the refer path costs more than the second bureau.”", [
 "V: Below about three hundred thousand applications a month, I would ship one bureau and refer. At two million a month, the refer path costs more than the second bureau does.", "[pause: 1.0]"])

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
