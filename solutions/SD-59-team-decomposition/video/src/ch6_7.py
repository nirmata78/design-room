from dsl import *
P = "[+]"

chapter(6, "Bridge", 4, "It works on paper. Where does it break first?", [
 "C: It works on paper. Where does it break first? Six places, ordered so each fix creates the next question: the critical path, a late dependency, a shared table, a contract dispute, a lost team, and finally how I would know any of it was going wrong."])

chapter(7, "Challenges", 5, "Six ways to break it, and what survives", [
 "C: Six challenges. For each: the question, the naive answer, the break on the component view, the fix one level down, and what I would say in the room."])

CH = []   # recorded for the Markdown design (one source: the slides' own arguments)
def challenge(n, title, intro, question, naive, bk, bk_say, fx, fx_title, fx_say, fix, why, rej, q2, second, say_voice):
    CH.append(dict(n=n, title=title, question=question, naive=naive, bk=bk, fx=fx, fix=fix, why=why, rej=rej, q2=q2, second=second, say=say_voice))
    subchapter(f"7.{n}", f"Challenge {n}: {title}", ["N: " + intro + " Roughly four minutes."])
    qs("Interviewer · challenge " + str(n), "“" + question + "”", ["I: " + question, "[pause: 2.0]"])
    S(plain(f"Challenge {n} · the naive answer", title, strip(("case", "Naive answer", naive[0]), ("whyb", "Why people say it", naive[1])), q=True, red=True), [
       "C: The first answer most people give: " + naive[0], P, "C: " + naive[1] + " Here is where it breaks."], cls="")
    S(dia(f"Challenge {n} · the break", "Where it breaks", bk, q=True, red=True, cap=f"Figure 7.{n}a — the failing case"), bk_say, cls="dia")
    S(dia(f"Challenge {n} · the fix", fx_title, fx, extra=strip(("fixb", "Fix", fix[0]), ("whyb", "Why it works", why)) + rejl(*rej), cap=f"Figure 7.{n}b — the fix"), fx_say, cls="dia")
    qs("Interviewer · what if the fix fails?", "“" + q2 + "”", ["I: " + q2, "[pause: 2.0]"])
    S(plain(f"Challenge {n} · the second fix", "The next mechanism, and its honest limit", cards(("grn", "Second fix", second[0]), ("amb", "What it costs", second[1]))), [
       "C: " + second[0], P, "C: " + second[1]])
    say_slide(say_voice[0], ["V: " + say_voice[1], "[pause: 1.0]"])

challenge(1, "Which team is on the critical path?", "Challenge one. Four teams need the ledger, and one team builds it.",
  "Which team is on the critical path, and what do the other four do while they work?",
  ("start everyone in parallel and let the teams sort it out.", "It sounds like autonomy, and it is the default when nobody names the path."),
  "bk-1", ["C: The break. Servicing core builds the ledger for months one to four.", P, "C: Collections waits for the ledger A-P-I.", P, "C: So does reconciliation.", P,
           "C: And so does policy. The ledger is the critical path, and three of five teams are queued behind it. With thirty-six engineer-months each, a month of waiting is a seventh of the budget."],
  "fx-1", "A contract and a mock in week two, then build in parallel",
  ["C: The fix, one level down. Servicing core publishes the ledger contract, version one, in week two, with the schema and examples.", P, "C: The contract hub generates a mock server from it.", P,
   "C: Collections builds against the mock.", P, "C: So does reconciliation.", P,
   "C: Fix: contract and mock in week two. This serves " + ps("L1") + ".", P,
   "C: Why it works: the consumers depend on the contract, not on the code, and the contract is stable enough to be built against from week two.", P,
   "C: Rejected: adding engineers to the ledger team. An interviewer will name it. It adds communication paths to a narrow interface, and the interface was the bottleneck."],
  ("Publish the ledger contract v1 and a generated mock in week two.", ""), "The consumers depend on the contract, not the code, so they build from week two, and the provider can still change what is behind it.",
  ("Adding engineers to the ledger team", "more communication paths on a narrow interface; the bottleneck is the contract, not typing speed"),
  "What if the mock drifts from the real service?",
  ("The mock is generated from the same contract file the provider's tests use, and the consumers' tests run against the real service nightly from month three.", "A nightly job and a provider fix time of two days; a drift is a failing test, not a surprise."),
  ("The critical path is the ledger", "The critical path is the ledger. I would publish its contract and a mock in week two, so the other four build in parallel, and I would own that date personally."))

challenge(2, "A dependency arrives two months late", "Challenge two. Team C needs team B's API in month two, and team B will not have it until month four.",
  "Team C needs Team B's API in month two, and B won't have it until month four. What do you do?",
  ("move team C's work to month four and let them wait.", "It is honest about the dependency, and it spends two months of a team's budget."),
  "bk-2", ["C: The break. Team C asks for the A-P-I in month two.", P, "C: Team B says not before month four.", P, "C: Team C is idle, or guesses the shape.", P,
           "C: In month four it integrates.", P, "C: And the shape was different. Two months spent, and re-work on top."],
  "fx-2", "Build against the registered calls, and let CI check them",
  ["C: The fix. Team C builds against the contract, version one.", P, "C: It registers the exact calls it makes in the hub.", P,
   "C: And team B's pipeline runs those calls against its real service, from the first day it exists.", P,
   "C: Fix: consumer-driven tests plus a mock. This serves " + ps("S1") + " and " + ps("L1") + ".", P,
   "C: Why it works: if B's real shape diverges, B's build fails and names C in week five, not in month four.", P,
   "C: Rejected: re-sequencing so C simply starts later. It spends two months of a thirty-six engineer-month budget on waiting."],
  ("Team C builds against contract v1; its calls are registered and run in B's CI.", ""), "A divergence fails B's own build and names C, in the week it happens, instead of both teams finding it in month four.",
  ("Re-sequencing: team C starts in month four", "it spends two of its thirty-six engineer-months on waiting and still integrates late"),
  "What if the real shape has to change after C started?",
  ("An additive version two with both live; C migrates by the sunset date, announced two weeks ahead.", "Two versions to support for a few weeks, and a sunset date the manager enforces."),
  ("Never idle, never surprised", "I would not let team C wait. They build against the contract in week two, and their calls run in B's pipeline from the day B's service exists, so a mismatch shows up as a failing build."))

challenge(3, "Two teams, one table, incompatible changes", "Challenge three. Two teams need incompatible changes to the same ledger table.",
  "Who owns the shared data model, and what happens when two teams need incompatible changes to it?",
  ("let them negotiate directly and merge whichever lands first.", "It assumes goodwill is a mechanism."),
  "bk-3", ["C: The break. Team B wants to rename a column.", P, "C: Team C wants to change its type.", P, "C: One table, two changes, the owner in the middle.", P,
           "C: Which goes first? With no rule, whoever shouts, and one team is broken in production."],
  "fx-3", "One owner, and versioned views instead of the table",
  ["C: The fix. Servicing core owns the ledger and its schema. That is " + ps("S2") + ".", P, "C: Collections reads a versioned view, not the table.", P, "C: Reconciliation reads the same view.", P,
   "C: The owner changes the table in three steps: expand with the new column, migrate readers to the new view, then contract the old one.", P,
   "C: Why it works: an incompatible need becomes two compatible versions, in sequence, decided by one owner.", P,
   "C: Rejected: a shared schema anyone may alter. An interviewer will name it. It has no owner, and the first long migration locks every team."],
  ("One owner; versioned views; expand, migrate, contract.", ""), "Two incompatible needs become two compatible versions, in order, and the order is one team's decision.",
  ("A shared schema every team may alter", "no owner, no order, and a long migration blocks everyone at once"),
  "What if the owner becomes a bottleneck?",
  ("The owner publishes a richer view so most needs need no change, reviews requests in two days, and hands a slice to a second team through its own contract if the queue passes five.", "Review time to staff, and a view layer to maintain."),
  ("One owner, versioned views", "Shared data gets exactly one owner. Everyone else reads versioned views. The owner changes a table by expanding, migrating, then contracting, so two incompatible needs become two compatible versions in order."))

challenge(4, "Two teams disagree on a contract", "Challenge four. Two teams disagree on a field, and both escalate to you.",
  "Two teams disagree on a contract and both escalate to you. Walk me through the conversation.",
  ("get both in a room and decide on the spot.", "It feels decisive, and it makes the manager the bottleneck."),
  "bk-4", ["C: The break. Team B wants a field required.", P, "C: Team D wants it optional.", P, "C: Team B escalates.", P, "C: Team D escalates.", P,
           "C: And I spend two hours in a meeting. Next month there is another dispute, and the same meeting."],
  "fx-4", "A written proposal, a clock, and a named decider",
  ["C: The fix. The provider writes a one-page decision record: the proposal and the options.", P, "C: The consumer has two days to object.", P,
   "C: The provider proposes an additive change: the old field stays.", P,
   "C: If they still disagree after five days, it comes to me.", P,
   "C: And my rule is that the provider decides, and the consumer's cost is recorded. Fix: a decision protocol. This serves " + ps("S1") + ".", P,
   "C: Why it works: most disputes dissolve in the written options; the rest have a clock and a decider, so I run a protocol, not a verdict.", P,
   "C: Rejected: a meeting with both teams. An interviewer will name it. It costs two hours a dispute, leaves no record, and the loser relitigates it."],
  ("A one-page decision record, a two-day objection window, the provider decides ties.", ""), "Most disputes dissolve when the options are written. The rest have a clock and a named decider, and the decision is on record.",
  ("Resolving it in a meeting with both teams", "two hours per dispute, no written record, and it is relitigated next sprint"),
  "What if the losing team is still unhappy?",
  ("The record names a revisit trigger, a number such as rejected calls in a month, rather than an argument.", "I look at the number at the month-three review; it takes discipline to let the data overrule the person who decided."),
  ("A protocol, not a verdict", "When two teams escalate, I run a protocol: a written proposal, two days to object, the provider decides, the consumer's cost is on record, and a number that reopens it. I am not the bottleneck."))

challenge(5, "You lose a team at month three", "Challenge five, the curveball. A reorg takes a whole team at month three.",
  "You lose one team entirely to a reorg at month three. What happens?",
  ("spread its work across the other four teams.", "It looks fair, and it spreads everyone thinner."),
  "bk-5", ["C: The break. The reorg takes team C at month three.", P, "C: Reconciliation and files are orphaned.", P,
           "C: The plan spreads everyone thinner.", P, "C: And now it is five teams of work for four teams. Every team gains an arrow and loses focus."],
  "fx-5", "Pause one component, freeze its contract, cut scope",
  ["C: The fix. Servicing core continues unchanged.", P, "C: Collections continues unchanged.", P,
   "C: Reconciliation is paused to the second release.", P, "C: Its contract stays frozen, so nobody built on it is affected.", P,
   "C: Fix: cut scope, not spread thin. This serves " + ps("S2") + " and " + ps("L1") + ".", P,
   "C: Why it works: the decomposition has one owner per component, so losing a team orphans one component, and a frozen contract makes that safe.", P,
   "C: Rejected: spreading the work across four teams. It adds four new arrows, and cuts every team's focus."],
  ("Pause reconciliation to release 2; freeze its contract; pair two engineers across A and B.", ""), "One owner per component means a lost team orphans one component, and a frozen contract means nothing built on it moves.",
  ("Spreading the orphaned work across the other four", "it adds four arrows and dilutes every team that was on track"),
  "What if the date cannot move?",
  ("Release one ships with manual break review in a sheet, an explicit risk product accepts in writing.", "Operations carry the manual work until release two, and the cost is stated, not hidden."),
  ("Cut scope, never spread thin", "If I lose a team, I pause its component, freeze its contract and cut scope. I do not spread the work across four teams. The decomposition was built so a lost team orphans exactly one thing."))

challenge(6, "How would you know the split is wrong?", "Challenge six, observability. How would you know, in month two, that the split is wrong?",
  "How do you know in month two that the decomposition is wrong, and how would you get this wrong?",
  ("watch the status reports.", "Everyone looks at them, and they are green until the date is missed."),
  "bk-6", ["C: The break. The dashboard says all green.", P, "C: In month two, nothing is integrated, and nobody has noticed.", P,
           "C: In month five, a two-month slip. Status reports measure what teams say, not what the split costs."],
  "fx-6", "Three leading indicators, read every week",
  ["C: The fix. Cross-team pull requests per week: when more than a quarter of pull requests need two teams, the seams are wrong.", P,
   "C: Lead time from idea to merged: if it doubles, a hand-off is hiding.", P,
   "C: Meeting hours per engineer: if it passes six a week, the arrows are being managed by talking.", P,
   "C: Together they give one split-health signal. Fix: leading indicators with thresholds. This serves " + ps("L3") + ".", P,
   "C: Why it works: they measure the cost of the cut, not a promise about it, and they move in weeks, before a date is missed.", P,
   "C: Rejected: status reports and colour codes. An interviewer will name them. They stay green until the date is missed."],
  ("Cross-team PRs, lead time and meeting hours, with thresholds set in advance.", ""), "They measure the cost of the cut itself and move within weeks, long before a date is missed.",
  ("Status reports and colour codes", "they report what teams say; they are green until the date is missed"),
  "How would you get this wrong yourself?",
  ("I designed the cut, so I will want it to be right. The thresholds are set now, a peer manager reads the dashboard with me, and one re-cut is allowed, once.", "A peer's time every month, and the humility to move a seam I drew."),
  ("Measure the cost of the cut", "In month two I would look at three numbers: cross-team pull requests, lead time and meeting hours, against thresholds set in advance. And I would name my own failure mode: I will want my cut to be right, so a peer reads the numbers with me."))


def md_challenges():
    out = []
    for c in CH:
        out += [f"## 6.{c['n']} {c['title']}", "", f"**Interviewer:** {c['question']}", "",
                f"**The naive answer.** {c['naive'][0].capitalize()} {c['naive'][1]}", "",
                f"![The failing case](diagrams/video-{c['bk']}.svg)", "",
                f"**The fix, one level down.** {c['fix'][0]} {c['why']}", "", f"![The fix](diagrams/video-{c['fx']}.svg)", "",
                f"> [!WARNING]\n> **Rejected: {c['rej'][0]}.** {c['rej'][1][0].upper() + c['rej'][1][1:]}.", "",
                f"**If the fix fails ({c['q2']})** {c['second'][0]} *Cost:* {c['second'][1]}", "",
                f"> [!TIP]\n> **If asked, I'd say:** {c['say'][1]}", ""]
    return "\n".join(out)
