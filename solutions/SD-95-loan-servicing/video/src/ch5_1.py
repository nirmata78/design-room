"""5.1 Components and technologies, built from ../stack.json (retrofit shape; SD-96 hand-writes the same slides).
Add `import ch5_1` after ch4_5 in gen.py. IDS = the stack entries to show, in order; DRILL boxes are the entries that carry a `drill`."""
from dsl import *
from stack import *
import json, pathlib
SVG = pathlib.Path(__file__).resolve().parents[1] / "svg"

subchapter("5.1", "Components and technologies", ["C: Now one level down. Every container, with the technology I would run it on, and for each choice, the alternatives I rejected and why."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech",
      cap="The container view with technologies; every choice has a rejected alternative on a later slide"), C4SAY(SVG), cls="dia")

S(dia("Architecture · C4 components · dispatcher", "Inside the box that spends the rails' budget", "c4-comp-dsp",
      cap="C4 level 3: the components challenges 1, 2 and 7 open"), [
 "C: One level further down, inside the box the challenges drill most: the dispatcher, a Go worker.",
 "[+]", "C: The servicing database holds the intents and the outbox.",
 "[+]", "C: The outbox poller claims sends by shard, with skip locked, so two workers never take the same row.",
 "[+]", "C: Every send passes the rail budgets: a token bucket per rail, with a live rate that halves the moment the rail throttles us.",
 "[+]", "C: The day plan sets those rates: windows planned backwards from each rail's cut-off.",
 "[+]", "C: Card sends go through the card client, with our idempotency key on every call. A timeout becomes unknown, never failed.",
 "[+]", "C: It calls the card processor's A-P-I.",
 "[+]", "C: Bank debits go through the file builder, which checks counts and totals before anything leaves,",
 "[+]", "C: and sends the file to the bank before the cut-off.",
 "[+]", "C: The result poster writes the outcome to the ledger by key, in one commit,",
 "[+]", "C: and hands every unknown to the resolver, a separate worker."], cls="dia")

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

# ───────── 5.2 · the alternate path (GUIDELINES §3.2) ─────────
subchapter("5.2", "When you don't need all this", ["C: Before I break it, the simpler design, and the number where it stops being enough."])

S(dia("Alternate path · one box changes", "One scheduled job, no rail budget", "alt",
      extra=strip(("case", "What it gives up", "No rate control: the processor's throttling decides. No day plan: a late file or a retry storm costs a day. Unknowns and returns are still handled."),
                  ("whyb", "The crossover", "One job at ≈ 10 card charges a second clears 36,000 in an hour: ≈ 180,000 collections due on the 1st at 20 % card. The scale line has 600,000."))), [
 "C: The alternate path changes one box. The ledger, the state machine with unknown and returned, and reconciliation all stay.",
 "[+]", "C: The dispatcher, marked alternate, becomes one scheduled job that walks the due items in order, one call at a time, and builds the file once a day.",
 "[+]", "C: What it gives up: there is no rate control, so the processor's throttling decides how fast we go, and there is no day plan, so a late file or a storm of retries costs a whole day. What it keeps matters more: unknown and returned are still states, and reconciliation still runs.",
 "[+]", "C: The crossover, from the scale line. One job at about ten card charges a second clears thirty-six thousand in an hour. At twenty percent on card, that is about a hundred and eighty thousand collections due on the first. The scale line has six hundred thousand, so this design would need three hours of card window and has no margin before the cut-off. Illustrative numbers."], cls="dia")

say_slide("“Below about two hundred thousand collections on the busiest day, I would ship one scheduled job. I would never ship without UNKNOWN, RETURNED and reconciliation.”", [
 "V: Below about two hundred thousand collections on the busiest day, I'd ship one scheduled job. I would never ship without unknown, returned and reconciliation.", "[pause: 1.0]"])
