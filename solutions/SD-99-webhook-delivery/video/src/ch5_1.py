"""5.1 Components and technologies, built from ../stack.json; 5.2 the alternate path."""
from dsl import *
from stack import *
import json, pathlib
SVG = pathlib.Path(__file__).resolve().parents[1] / "svg"

subchapter("5.1", "Components and technologies", ["C: Now one level down. Every container with the technology I would run it on, including the three the challenges will add, and for each choice, the alternatives I rejected and why."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech",
      cap="The container view with technologies; the three marked NEW arrive with challenges 3, 5 and 6"), C4SAY(SVG), cls="dia")

S(dia("Architecture · C4 components · dispatcher", "Inside the box where isolation lives", "c4-comp-dsp",
      cap="C4 level 3: challenges 2, 3 and 5 are drawn on this view"), [
 "C: One level further down, inside the dispatcher, the box challenges two, three and five will open.",
 "[+]", "C: Due rows come from the delivery store.",
 "[+]", "C: The claimer takes them with skip locked and a lease, and only for endpoints under their cap.",
 "[+]", "C: Tier pools are bulkheads: the partner bank, large merchants and the long tail never share workers.",
 "[+]", "C: The endpoint limiter is a semaphore per endpoint: ten calls in flight by default.",
 "[+]", "C: A breaker per endpoint opens after five failures in a row.",
 "[+]", "C: The H-T-T-P client has a two-second connect timeout, a ten-second total, keep-alive, and reads at most four kilobytes of any answer.",
 "[+]", "C: The signer computes an H-MAC over the event I-D, the timestamp and the body,",
 "[+]", "C: with the endpoint's secret from the key service, cached for five minutes.",
 "[+]", "C: Every call leaves through the egress proxy.",
 "[+]", "C: The result writer marks the row delivered, or writes its next attempt time,",
 "[+]", "C: and reports the outcome to the endpoint health loop."], cls="dia")

S(dia("Architecture · C4 components · fan-out", "Where order by loan becomes isolation by endpoint", "c4-comp-fan",
      cap="C4 level 3: challenges 4 and 6 are drawn on this view"), [
 "C: And inside fan-out, which challenges four and six open.",
 "[+]", "C: Events arrive from the log, ordered by loan.",
 "[+]", "C: The log consumer commits its offset only after its batch is written, so a crash repeats a batch.",
 "[+]", "C: Subscription changes come from the webhooks A-P-I,",
 "[+]", "C: into an in-memory cache.",
 "[+]", "C: The matcher turns one event into N endpoints by type and merchant.",
 "[+]", "C: The renderer turns the internal event into each endpoint's pinned public version,",
 "[+]", "C: from the schema registry, which arrives in version six.",
 "[+]", "C: The payload writer stores each event once, not once per delivery.",
 "[+]", "C: The sequence check carries the producer's sequence number for the loan.",
 "[+]", "C: The delivery writer inserts rows in batches, unique on endpoint and event, so a repeated batch is absorbed,",
 "[+]", "C: into the delivery store."], cls="dia")

for _id in [s["id"] for s in DATA["stack"]]:
    S(tech(**TECH(_id)), SAY(_id))

S(plain("Technology · the stack on one slide", "The stack, against its rivals",
        table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
        grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), SUMMARY_SAY())

qs("Coach · your turn", "You are the interviewer. Which box would you drill, and what is your one question?", [
 "N: Before the challenges, swap seats. You are the interviewer now. Of everything on the last slide, which box would you push on, and what is the one question you would ask? Pause the video and pick one.", "[pause: 3.0]"])

S(plain("Drill · one level down", "The question each box invites",
        table(["Box", "The probe", "A strong answer names"], DRILL(), "bt xs mx") +
        grade("The probe lands on the box you named. The score is set where your answer runs out.")), DRILL_SAY())

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
subchapter("5.2", "When you don't need all this", ["C: Before I break it, the simpler design. At this scale it is a serious option, and saying so is part of the answer."])

S(dia("Alternate path · one box changes", "Buy the delivery engine, keep the contract", "alt",
      extra=strip(("case", "What it gives up", "Loan-level data leaves for a vendor the partner bank must approve; caps and tiers are the vendor's; cost grows per message."),
                  ("whyb", "The crossover", "180 M × $0.10 per thousand ≈ $18k a month, against ≈ $80k for a team of three and its infrastructure: building wins past ≈ 800 M deliveries a month."))), [
 "C: The alternate path changes one box. Our outbox, our log, fan-out and the public contract stay ours.",
 "[+]", "C: The dispatcher, marked alternate, becomes a managed webhook service: it stores, signs, retries and shows merchants their logs.",
 "[+]", "C: What it gives up, precisely: loan-level data now leaves for a vendor, and the partner bank's vendor-risk review must approve that. The isolation caps and tiers are the vendor's, not ours. And the cost grows with every message.",
 "[+]", "C: The crossover, from the scale line. A hundred and eighty million deliveries a month, at an illustrative ten cents a thousand, is about eighteen thousand dollars a month. A team of three with on-call and infrastructure costs about eighty. On cost alone, building wins only past about eight hundred million deliveries a month."], cls="dia")

say_slide("“At a hundred and eighty million a month I would seriously consider buying the delivery engine and keeping the outbox, the log and the contract. I build when the bank will not let the data leave, or past eight hundred million.”", [
 "V: At a hundred and eighty million deliveries a month, I would seriously consider buying the delivery engine, and keep the outbox, the log and the contract. I'd build when the partner bank won't let loan-level data leave, or past about eight hundred million a month.", "[pause: 1.0]",
 "N: Saying that is not a weakness in a design round. It is the build-against-buy judgement the manager layer is graded on. The rest of this video designs the build, because that is where the mechanisms are."])
