from dsl import *

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 5 · a burst, seconds apart ─────────
subchapter("7.5", "Challenge 5: A burst, seconds apart", ["N: Challenge five. A rule counts swipes in ten minutes: where does that count come from, and how old is it when we read it?"])
qs("Interviewer · challenge 5 of 8", "“Your rule is more than three swipes in ten minutes on one card. Where does that number come from, in time?”", [
 "I: Your rule is more than three swipes in ten minutes on one card. Where does that number come from, in time?", "[pause: 2.0]"])

S(dia(K(5, "the burst"), "Counters that arrive after the fraud", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“From the stream processor, into a key-value store.”"),
                  ("case", "Break", "The stream aggregator feeding the feature store: correct, and seconds late."))), [
 "C: The naive answer: a stream processor counts swipes and writes them to a key-value store. The red stream aggregator is correct, and seconds late."], cls="dia")

S(plain(K(5, "the trace"), "Four swipes in eight seconds, read as zero, one, one, two", '<pre class="trace"><span class="t">03:12:01</span>card-not-present $240 on token T-55: the counter reads 0 → approve\n<span class="t">03:12:04</span>$240: reads 1 → approve\n<span class="t">03:12:06</span>$240: reads 1 → approve\n<span class="t">03:12:09</span>$240: reads 2 → approve\n<span class="t">03:12:15</span>the counter finally reads 4: <span class="bad">$960 already gone</span></pre>' +
  '<div class="hedge"><b class="t">Why</b>A burst of fraud on one stolen card is a script: seconds apart. A stream is seconds behind: that is what streams are.</div>', q=True, red=True), [
 "C: The trace. At twelve minutes past three in the morning, four card-not-present purchases of two hundred and forty dollars on one token, within eight seconds. The stream's counter is five to eight seconds behind, so the four decisions read zero, one, one and two. All approved. Six seconds later the counter reads four, and nine hundred and sixty dollars are gone.",
 "C: A burst on one stolen card is a script, seconds apart. A stream is seconds behind. That's what streams are."])

S(dia(K(5, "the fix"), "Burst counters inline; patterns from the stream", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "Per card, one-minute buckets: increment this minute and read the nine before, in one pipelined round trip, about 1 ms, before deciding."),
                  ("whyb", "Property", "Exact at decision time for the features whose value is being now. S3: every value is logged with the decision."))), [
 "C: The fix. Burst counters are updated inline, by the decision service itself: per card, one-minute buckets. Before deciding, increment this minute and read the nine before it, in one pipelined round trip, about a millisecond. The counter now reads one, two, three, four, and the fourth swipe is declined."], cls="dia")

S(dia(K(5, "two kinds of features"), "Exact now, or richer and seconds late", "features"), [
 "C: Two kinds of features. Inline, on the request path: swipes on this card in ten minutes, card-not-present spend in the last hour, declines in the last hour. From the stream, seconds late, which is fine for them: distinct merchants for this card today, a merchant's decline rate in the last hour, a device seen on other cards in thirty days. The decision reads both in the same call."], cls="dia")

S(plain(K(5, "the counter, as code"), "Count this swipe, then read ten minutes",
  '<pre class="code" data-lang="python"><span class="kw">def</span> swipes_10m(store, token, now_s):\n    minute = now_s // 60\n    key = f<span class="st">"v:{token}:{minute}"</span>\n    pipe = store.pipeline(transaction=True)\n    pipe.incr(key)                       <span class="cm"># this swipe</span>\n    pipe.expire(key, 11 * 60)            <span class="cm"># buckets clean up</span>\n    <span class="kw">for</span> m <span class="kw">in</span> range(minute - 9, minute):\n        pipe.get(f<span class="st">"v:{token}:{m}"</span>)       <span class="cm"># the nine before</span>\n    res = pipe.execute()\n    <span class="kw">return</span> res[0] + sum(int(x <span class="kw">or</span> 0) <span class="kw">for</span> x <span class="kw">in</span> res[2:])</pre>' +
  strip(("whyb", "Two details", "The swipe is counted before the decision, so declined attempts count: a script that keeps trying is the strongest signal. And every value goes into the decision record, so training sees what the model saw."), cols="one")), [
 "C: In code. One key per card per minute, with an expiry of eleven minutes so the buckets clean themselves up. In one pipelined round trip: increment this minute, read the nine before, and sum.",
 "C: Two details. The swipe is counted before the decision, so declined attempts count too, and a script that keeps trying after a decline is the strongest signal there is. And every feature value goes into the decision record, so the model is trained on exactly what it saw, not on values recomputed later by a different pipeline."])

qs("Interviewer · the second-level push", "“The counter store is slow or down.”", [
 "I: The counter store is slow, or down.", "[pause: 2.0]"])

S(plain(K(5, "the second fix"), "It is a row in the fail table", '<div class="cards c2">'
  '<div class="cd grn"><h3>Decide without it</h3><p>Counters missing: rules with conservative card-not-present limits, inside the cap. Card-present purchases barely change.</p></div>'
  '<div class="cd amb"><h3>Rebuild it</h3><p>Partitioned by card, with a replica. Losing a partition loses ten minutes of buckets, rebuilt from the event log for the cards that transact next.</p></div></div>'), [
 "C: It is already a row in the fail table: counters missing, so rules apply conservative limits for card-not-present, inside the cap. Card-present purchases barely change.",
 "C: And the store is partitioned by card with a replica. Losing a partition loses at most ten minutes of buckets, which are rebuilt from the event log for the cards that transact next."])

say_slide("“Burst features are counted inline, read and incremented in one round trip, because a stream lags behind a burst. Pattern features come from the stream. And every value is logged with the decision, so training sees what the model saw.”", [
 "V: If asked, I'd say: burst features are counted inline, in one round trip, because a stream lags behind a burst. Patterns come from the stream, and every value is logged with the decision.", "[pause: 1.0]",
 "N: A counter is only useful if a rule reads it. The next question is how a rule gets there, at two in the morning."])

# ───────── Challenge 6 · a new attack at 2 a.m. ─────────
subchapter("7.6", "Challenge 6: A new attack at 2 a.m.", ["N: Challenge six. An attack starts in the middle of the night: how fast can an analyst block it, and what stops them blocking everyone?"])
qs("Interviewer · challenge 6 of 8", "“A new attack appears at two in the morning. How fast can an analyst block it, and what stops them from blocking everyone?”", [
 "I: A new attack appears at two in the morning. How fast can an analyst block it, and what stops them from blocking everyone?", "[pause: 2.0]"])

S(dia(K(6, "the 2 a.m. attack"), "Too slow, or too blunt", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answers", "“Add an if and hotfix the service.” Or: “Shadow-test it to measure the false positives.”"),
                  ("case", "Break", "The rule path into the decision service: either a deploy, or a live change with no safety."))), [
 "C: Two naive answers. Add an if-statement and hotfix the decision service. Or: shadow-test the rule to measure its false positives. The red rule path is either a deploy, or a live change with nothing in between."], cls="dia")

S(plain(K(6, "the trace"), "Fifty minutes, or nine percent of good customers", '<pre class="trace"><span class="t">02:05</span>pattern: a $1 test charge, then $400 at electronics merchants, cards from one breach\n<span class="t">hotfix</span>review, build, deploy → <span class="bad">live at 02:55; fifty minutes of losses</span>\n<span class="t">02:20</span>an analyst pushes amount > 300 and electronics → decline, live\n<span class="t">02:21</span><span class="bad">9 % of all electronics purchases declined, almost all good customers</span></pre>', q=True, red=True), [
 "C: The trace. Five past two: fraud operations see a pattern. A one-dollar test charge, then four hundred at electronics merchants, on cards from one breach. A hotfix goes through review, build and deploy, and is live at five to three: fifty minutes of losses.",
 "C: The other way: at twenty past two an analyst pushes amount over three hundred at electronics, decline, straight to production. A minute later, nine percent of all electronics purchases are declined, almost all of them good customers."])

S(dia(K(6, "the fix"), "Rules as versioned data, staged", "ch6-fix", chip=chips("fix: backtest → shadow → slice → enforce", "version on every decision", "property: L3, S3")), [
 "C: The fix: rules are versioned data. A rule is an expression in a small sandboxed language, with an owner and an expiry. It goes through four stages, and every decision records the rule-set version it ran."], cls="dia")

S(dia(K(6, "the lifecycle"), "Fast, measured, and undoable", "rule-life"), [
 "C: The stages. Write the expression. Backtest it on ninety days of the decision archive, with known labels: how much of this ring it catches, how many good purchases it declines. Shadow: it runs on live traffic and logs what it would have done. A slice: enforce on five percent, with an alarm on the decline rate by merchant type. Then enforce everywhere, with a kill switch.",
 "C: Rollback is re-pointing every decision service to the previous rule-set version: seconds, no deploy."], cls="dia")

S(plain(K(6, "a rule, as data"), "Versioned, reviewed, evaluated in a sandbox",
  '<pre class="code" data-lang="yaml"><span class="kw">id:</span> test-then-electronics\n<span class="kw">version:</span> 15\n<span class="kw">condition:</span> &gt;\n  txn.entry_mode == <span class="st">"card_not_present"</span>\n  &amp;&amp; txn.mcc in [<span class="st">"5732"</span>, <span class="st">"5734"</span>]\n  &amp;&amp; txn.amount &gt; 300\n  &amp;&amp; features.small_charges_24h &gt;= 1\n<span class="kw">action:</span> decline\n<span class="kw">mode:</span> shadow        <span class="cm"># shadow | slice | enforce</span>\n<span class="kw">slice:</span> 0.05\n<span class="kw">expires:</span> 2026-12-05\n<span class="kw">owner:</span> fraud-ops/night</pre>'), [
 "C: A rule, as data. An identifier and a version. The condition: card-not-present, at electronics merchant categories, over three hundred dollars, and at least one small charge on the card in the last day. That last clause is what makes it narrow. An action, a mode, a slice, an expiry two weeks out, and an owner. The language has no loops and no input or output, and each evaluation has a time limit, so a bad rule cannot hang the decision."])

qs("Interviewer · the second-level push", "“Shadow says the rule would decline 4,000 transactions a day. How many were fraud?”", [
 "I: Shadow says the rule would decline four thousand transactions a day. How many were fraud?", "[pause: 2.0]"])

S(plain(K(6, "the honest limit"), "Shadow cannot say: labels arrive in 30 to 90 days", '<div class="cards c2">'
  '<div class="cd red"><h3>What shadow shows</h3><p>How many it would decline today, and its overlap with existing rules. Not which were fraud: chargebacks arrive weeks later, and most declined good customers never complain.</p></div>'
  '<div class="cd grn"><h3>What to use instead</h3><p>Backtests on labelled history. Fast proxies: “it was me” replies to a decline text; step-up pass rates. A small slice with an alarm. And the expiry, so the rule is reviewed with real labels.</p></div></div>'), [
 "C: Shadow cannot say. It shows how many it would decline, not which were fraud, because the labels, chargebacks and customer reports, arrive thirty to ninety days later. And most declined good customers never complain at all; they use another card.",
 "C: So the evidence comes from elsewhere. Backtests on labelled history. Fast proxies: the share of customers who reply it was me to a decline text, or who pass a step-up. The slice with its alarm. And the expiry, so an emergency rule is reviewed with real labels instead of living forever."])

say_slide("“Rules are versioned data, not code: backtest, shadow, a small slice with a decline-rate alarm, then enforce, with a kill switch and the version on every decision. Shadow can't measure false positives, because labels arrive months later.”", [
 "V: If asked, I'd say: rules are versioned data: backtest, shadow, a small slice with an alarm, then enforce, with the version on every decision. Shadow can't measure false positives; labels arrive months later.", "[pause: 1.0]",
 "N: Everything so far assumed we were up to answer. The next question is what happens when we were not."])

# ───────── Challenge 7 · we were down for twenty minutes ─────────
subchapter("7.7", "Challenge 7: We were down for twenty minutes", ["N: Challenge seven. The network decided for us during an outage: what does the next morning look like, and what if the clearing file is bad too?"])
qs("Interviewer · challenge 7 of 8", "“You were down for twenty minutes at two in the morning. The network approved 360,000 transactions in stand-in. Walk me through the next morning.”", [
 "I: You were down for twenty minutes at two in the morning. The network approved three hundred and sixty thousand transactions in stand-in. Walk me through the next morning.", "[pause: 2.0]"])

S(dia(K(7, "stand-in"), "An invariant that refuses the network's decisions", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answers", "“The network declined them while we were down.” Or: “Replay them and decline the ones we wouldn't have approved.”"),
                  ("case", "Break", "A never-below-zero check on the advice path rejects what the network already did."))), [
 "C: Two naive answers. The network declined everything while we were down. It didn't: it approved, within our limits. Or: replay them and decline the ones we would not have approved. Too late: the purchases happened. The red path refuses advices that break a never-below-zero rule."], cls="dia")

S(plain(K(7, "the trace"), "Account A-19, and books that disagree", '<pre class="trace"><span class="t">02:00–02:20</span>stand-in approves within our limits: up to $150 a purchase, $400 a day a card\n<span class="t">02:21</span>we are back; 360,000 advices arrive\n<span class="t">02:21</span>A-19 had $35 available; stand-in approved $60 and $80 → available −$105\n<span class="t">02:21</span><span class="bad">a never-below-zero check rejects both advices: no holds</span>\n<span class="t">Thu 06:00</span><span class="bad">clearing posts both anyway; our books disagree with the network\'s</span></pre>', q=True, red=True), [
 "C: The trace. From two to twenty past, stand-in approves within our limits: say up to a hundred and fifty dollars a purchase, four hundred a day a card. Twenty minutes, at three hundred a second, is three hundred and sixty thousand approvals.",
 "C: At twenty-one minutes past, we are back, and the advices arrive. Account A-nineteen had thirty-five dollars available, and stand-in approved sixty and eighty. Available is minus one hundred and five. A check that refuses any write below zero rejects both advices. No holds. On Thursday clearing posts both anyway, and our books disagree with the network's."])

S(dia(K(7, "the fix"), "Record every advice once, even when it overdraws", "ch7-fix", chip=chips("fix: record every advice once", "over-limit is a modelled state", "property: S2; S1 is about our approvals")), [
 "C: The fix: the ledger absorbs the decisions we did not make. Every advice is acknowledged and recorded once, by its network reference, as a hold, even when it takes the account below zero. Over-limit is a modelled account state. New authorisations on that account decline until it is back above zero, the customer is told, and collections take over if it persists."], cls="dia")

S(dia(K(7, "sequence"), "Advices after the outage", "seq-ch7-advices"), [
 "C: As a sequence. Advice R-fifty-one-oh-two, eighty dollars, approved by stand-in. Record it as a hold, even past available. Account A-nineteen: available minus one hundred and five, state over-limit. Acknowledge. An event goes to the ledger. And new authorisations on A-nineteen decline until it is paid back.",
 "C: Then, in the morning, replay the three hundred and sixty thousand through our rules offline. Not to reverse them. To see which we would have declined, and to tune the stand-in limits with risk."], cls="dia")

S(plain(K(7, "the morning after"), "Replay the night to tune the stand-in limits", table(["Question", "From the replay"], [
  ["Which stand-in approvals would we have declined?", "say 2.1 % of the 360,000 (illustrative)"],
  ["How much of that turns out to be fraud?", "known only as labels arrive, weeks later"],
  ["Were the limits too high, or too low?", "set with risk: fewer declined good customers against more fraud let through"]], "bt") +
  line("The replay never reverses a purchase. It is the only data that says whether last night's limits were right.", "a")), [
 "C: The morning after, the replay. Run the three hundred and sixty thousand through our rules and model offline, and ask which we would have declined. Say two percent, an illustrative number. How much of that was fraud, we only learn as labels arrive. And then, with risk, decide whether the stand-in limits were too high or too low: fewer good customers declined during an outage, against more fraud let through.",
 "C: The replay never reverses a purchase. It is simply the only data that says whether last night's limits were right."])

qs("Interviewer · the second-level push", "“And the next day's clearing file arrives six hours late, with 3 % of its records duplicated.”", [
 "I: And the next day's clearing file arrives six hours late, with three percent of its records duplicated.", "[pause: 2.0]"])

S(plain(K(7, "the second fix"), "Idempotent files, and expiry that waits", '<div class="cards c3">'
  '<div class="cd grn"><h3>Idempotent ingestion</h3><p>A checksum per file; a unique ID per record. 3 % × 10 M = 300,000 duplicates become no-ops.</p></div>'
  '<div class="cd amb"><h3>Expiry waits</h3><p>Holds past their lifetime are released only after the day\'s file is in, so a late file finds its holds still open.</p></div>'
  '<div class="cd"><h3>Reconcile daily</h3><p>Posted in the auth store must equal the ledger, per account. Any difference is a break with an owner. The 09:00 target slips with a note, not silently.</p></div></div>'), [
 "C: Ingest files idempotently: a checksum per file, so a resent file is recognised, and a unique I-D per record, so the three hundred thousand duplicates are no-ops. Hold expiry waits for the day's file, so a file six hours late still finds its holds open.",
 "C: The nine o'clock posting target slips, with a note to finance and support, not silently. And every day after clearing, the authorisation store is reconciled with the ledger, account by account. Any difference is a break with an owner."])

say_slide("“Stand-in decisions are facts, not requests: we record every advice once, even when it overdraws the account, and model over-limit as a state. Clearing files are ingested idempotently, and hold expiry waits for the day's file.”", [
 "V: If asked, I'd say: stand-in decisions are facts, not requests. We record every advice once, even when it overdraws, and model over-limit as a state. Files are idempotent, and expiry waits for them.", "[pause: 1.0]",
 "N: Last question, and the one every challenge depends on: how would we know any of this was happening?"])

# ───────── Challenge 8 · declines doubled ─────────
subchapter("7.8", "Challenge 8: Declines doubled in ten minutes", ["N: Challenge eight. The decline rate doubles and every dashboard is green: how do we find out, and what do we do first?"])
qs("Interviewer · challenge 8 of 8", "“The decline rate doubled in ten minutes. Your dashboards are green. How do you know what is wrong, and what is on the runbook?”", [
 "I: The decline rate doubled in ten minutes. Your dashboards are green. How do you know what is wrong, and what is on the runbook?", "[pause: 2.0]"])

S(dia(K(8, "declines doubled"), "Healthy boxes, a broken product", "ch8-attack", q=True, red=True, chip=chips("naive: CPU, errors, latency", "break: nothing watches the decisions")), [
 "C: The naive answer: C-P-U, error rate and latency. Those watch boxes. The red rule service and decision service are perfectly healthy, and wrong."], cls="dia")

S(plain(K(8, "the trace"), "Nothing failed for half an hour", '<pre class="trace"><span class="t">19:40</span>rule set v212 enforced: a typo widens a merchant list to include groceries\n<span class="t">19:41</span>grocery approvals 96 % → 71 %; no errors; p99 92 ms\n<span class="t">19:55</span><span class="bad">the first complaints on social media</span>\n<span class="t">20:10</span><span class="bad">the first page, from support call volume</span></pre>', q=True, red=True), [
 "C: The trace. Twenty to eight: rule set two hundred and twelve is enforced, and a typo widens a merchant list to include groceries. A minute later, grocery approvals fall from ninety-six percent to seventy-one. No errors. Latency ninety-two milliseconds. At five to eight, the first complaints on social media. At ten past, the first page, from support call volume. Half an hour, and nothing failed."])

S(dia(K(8, "the fix"), "Watch decisions, not machines", "ch8-fix", chip=chips("fix: approval rate by merchant type vs last week", "stand-in count", "test cards", "pages at 19:42")), [
 "C: The fix: indicators on decisions, not machines. Approval rate by merchant type and region, every minute, against the same hour last week, because card traffic is strongly weekly. The stand-in count. Degraded decisions against each cap. And synthetic test cards in every region that authorise and reverse every minute, end to end. This one pages at nineteen forty-two."], cls="dia")

S(plain(K(8, "symptom pairs"), "Two metrics, one cause", table(["When you see", "Together with", "It means"], [
  ["Declines up", "a rule-set change in the same minute", "<b>a rule</b> (this trace)"],
  ["Declines up in one merchant", "flat everywhere else", "<b>that merchant's terminal or acquirer</b>"],
  ["Stand-in up", "gateway p99 flat", "<b>the link to the processor</b>, not us"],
  ["Model cut-offs up", "p99 flat", "<b>the model</b>; the cut-off is working"],
  ["“It was me” up", "declines up", "<b>false positives</b>: roll back"],
  ["Declines up", "“it was me” flat, step-up pass low", "<b>a real attack</b>: keep the rule"]], "bt sm")), [
 "C: Symptom pairs: two metrics, one cause. Declines up with a rule-set change in the same minute: a rule, this trace. Declines up at one merchant only: that merchant's terminal. Stand-in up while our latency is flat: the link to the processor, not us. Model cut-offs up with flat latency: the model, and the cut-off is doing its job.",
 "C: And the pair that settles the argument: declines up with it-was-me replies up means false positives, roll back. Declines up with it-was-me flat and step-ups failing means a real attack: keep the rule."])

S(plain(K(8, "the runbook"), "Declines doubled in ten minutes", table(["Step", "Why"], [
  ["1 Rule-set and release changes in the last hour", "the most common cause, and the fastest to undo"],
  ["2 Re-point to the previous rule-set version", "rollback in seconds, no deploy"],
  ["3 Compare by merchant type and region", "a real attack, or one merchant's broken terminal?"],
  ["4 Then the model and its features", "a stale feature looks like risk"],
  ["5 Tell support and the status page", "otherwise complaints arrive before alerts"]], "bt")), [
 "C: The runbook. First, rule-set and release changes in the last hour: the most common cause and the fastest to undo. Second, re-point to the previous version, in seconds. Third, compare by merchant type and region, to tell an attack from one broken terminal. Fourth, the model and its features, because a stale feature looks like risk. And fifth, tell support, because otherwise the complaints arrive before the alerts."])

qs("Interviewer · the second-level push", "“It's real fraud this time: an attack, and the rule is right.”", [
 "I: It's real fraud this time. An attack, and the rule is right.", "[pause: 2.0]"])

S(plain(K(8, "the second fix"), "Let the customers' answers decide", '<div class="cards c2">'
  '<div class="cd grn"><h3>Separate good from bad in minutes</h3><p>If few declined customers reply “it was me” and few pass a step-up, the rule is right.</p></div>'
  '<div class="cd amb"><h3>Then keep it, and say so</h3><p>Tell support what customers will hear; the expiry brings the rule back for review with real labels.</p></div></div>'), [
 "C: Then the it-was-me rate and the step-up pass rate separate good customers from fraud within minutes. If few declined customers say it was them, and few pass a step-up, the rule is right. Keep it, tell support what customers will hear, and let the expiry bring it back for review."])

say_slide("“I watch decisions, not boxes: approval rate by merchant type against last week, stand-in count, degraded decisions against the cap. The runbook starts with what changed, because a rule or a release is the usual cause and the fastest to undo.”", [
 "V: If asked, I'd say: I watch decisions, not boxes. Approval rate by merchant type against last week, and stand-in count. The runbook starts with what changed, the usual cause and the fastest to undo.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost ─────────────────────────
chapter(8, "Build cost", 6, "Who, how long, buy or build: the manager layer", [
 "C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round."], aux=True)

S(plain("Build cost · four releases", "Start by buying", table(["", "V0 · buy", "V1", "V2", "V3"], [
  ["Scope", "the processor decides with our uploaded rules and stand-in limits", "own decision service on the core ledger", "auth store, rules as data, model with a cut-off, clearing matcher", "features, fail table, advices, lifecycle tooling, reconciliation"],
  ["People", "3", "4", "a team of 6–8", "two teams"],
  ["Time", "8 weeks", "3 months", "2 quarters", "2 more quarters"]], "bt sm")), [
 "C: Four releases, starting by buying. Version zero: the processor decides, with rules and stand-in limits we upload. Three engineers, eight weeks, and fine for a launch. Version one: our own decision service on the core ledger, four engineers, three months.",
 "C: Version two: the authorisation store, rules as data, the model behind a cut-off and the clearing matcher, a team of six to eight for two quarters. Version three: features, the fail table, advices, lifecycle tooling and reconciliation, two teams for two more quarters."], cls="aux")

S(plain("Build cost · team seams", "Five owners, three contracts", '<div class="cards c3">'
  '<div class="cd"><h3>Authorisation platform</h3><p>Gateway, decision service, auth store; latency and availability.</p></div>'
  '<div class="cd grn"><h3>Risk platform</h3><p>Rules engine, features, backtest and shadow tooling.</p></div>'
  '<div class="cd amb"><h3>Data science · fraud ops · ledger</h3><p>Models; rule content and customer contact; posting and reconciliation.</p></div></div>' +
  line("The contracts: the decision event schema, the rule-set format, and the fail-policy table.", "a")), [
 "C: Team seams. The authorisation platform owns the gateway, the decision service and the store, and their latency. The risk platform owns the rules engine, features and the shadow tooling. Data science owns models. Fraud operations own the content of the rules and customer contact. Ledger and clearing own posting and reconciliation.",
 "C: The contracts between them are three: the decision event schema, the rule-set format, and the fail-policy table."], cls="aux")

S(plain("Build cost · buy, build, and cost", "A basis point of fraud outweighs the fleet", '<div class="cards c2">'
  '<div class="cd"><h3>Buy against build</h3><p>Bought: the processor and its card vault; perhaps the model platform. The network\'s own risk score is an input. Built: the decision path, holds and clearing match, because they are the product.</p></div>'
  '<div class="cd amb"><h3>Cost, illustrative</h3><p>Largest: per-transaction fees and fraud losses at 8 bps of volume. Then the decision archive, 15 TB a year, and model serving. The fleet is small.</p></div></div>'), [
 "C: Buy against build. We buy the processor and its card vault, and perhaps the model platform; the network's own risk score arrives as an input. We build the decision path, holds and the clearing match, because they are the product.",
 "C: Cost, illustrative. The largest lines are per-transaction fees and fraud losses, eight basis points of volume. Then the archive and model serving. The fleet is small. A basis point of fraud is worth more than all the servers, so the cost lever is the quality of the decision."], cls="aux")

S(plain("Build cost · top risks", "What I'd put on the risk register", table(["Risk", "Mitigation"], [
  ["A fail policy nobody signed", "the table and caps reviewed monthly by risk and finance"],
  ["The auth store and the ledger drifting", "daily reconciliation, breaks with owners"],
  ["Emergency rules living forever", "an expiry on every rule"],
  ["Card data creeping into scope", "tokens only, enforced at the gateway"]], "bt")), [
 "C: Top risks. A fail policy nobody signed: review the table and caps monthly. The store and the ledger drifting: reconcile daily. Emergency rules living forever: an expiry on every rule. And card data creeping into scope: tokens only, enforced at the gateway."], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, four paths, the mistakes, the thesis", [
 "C: To close: one picture, one sentence per path, the mistakes to avoid, and the thesis."])

S(dia("Recap", "The whole design on one baseline", "base-final", chip=chips("holds", "network reference", "per-account reserve", "cut-off + fail table", "inline counters", "rules as data", "advices", "probes")), [
 "C: The final picture. Across the middle: the network, the gateway, the decision service with rules in process, and the authorisation store with its one atomic reserve. Above: the model behind a cut-off, the feature store with inline counters, the stream aggregator, and the rule service. Below: the event log, alerts and the archive, the clearing matcher feeding the ledger, and probes with test cards."], cls="dia")

S(plain("Recap · one sentence per path", "Four paths", table(["Path", "In one sentence"], [
  ["<b>Authorise</b>", "Counters, rules and model in parallel under a budget; one atomic reserve; an answer in time"],
  ["<b>Reverse and advise</b>", "By reference, in any order; record what the network decided, even when it hurts"],
  ["<b>Clear</b>", "The file is the truth: match, move hold to posted, post, expire after the file"],
  ["<b>Change rules</b>", "Data, versioned, staged, and recorded on every decision"]], "bt")), [
 "C: Four paths, one sentence each. Authorise: counters, rules and the model under a budget, one atomic reserve, an answer in time. Reverse and advise: by reference, in any order, and record what the network decided. Clear: the file is the truth. Change rules: data, versioned, staged, recorded on every decision."])

S(plain("Recap · eight fixes", "Each names the property it protects", table(["Challenge", "Fix", "Property"], [
  ["1 The tip", "holds; clearing moves the money; expiry", "S1, L2"],
  ["2 Two swipes", "one conditional write per account", "<b>S1</b>"],
  ["3 Twice, out of order", "network reference; tombstones; same transaction", "<b>S2</b>"],
  ["4 Slow model", "cut-off; fail table; caps and owners", "<b>L1</b>"],
  ["5 A burst", "inline counters; features logged", "quality, S3"],
  ["6 2 a.m. attack", "rules as data, staged; expiry", "L3, S3"],
  ["7 Stand-in", "record advices even past zero; idempotent files", "S2, L2"],
  ["8 Declines doubled", "decision SLIs; symptom pairs; runbook", "all"]], "bt sm")), [
 "C: Eight fixes, each with its property. Holds for the tip. One conditional write per account. The network reference, with tombstones. A cut-off and a fail table with caps. Inline counters. Rules as staged data. Recording every advice. And watching decisions, not boxes."])

S(plain("Recap · common mistakes in this round", "Ten ways this round goes wrong", '<div class="cards c2"><div class="cd red"><h3>Design</h3><ul style="font-size:16pt"><li>Debit at authorisation</li><li>One authorisation, one clearing record</li><li>Read, then write, on the balance</li><li>Ignoring retries and early reversals</li><li>Velocity only from a stream</li></ul></div>'
  '<div class="cd amb"><h3>Judgment</h3><ul style="font-size:16pt"><li>“The network gives us 100 ms”</li><li>Waiting for the model, or “fail open” as the whole answer</li><li>Shadow mode to measure false positives</li><li>Refusing advices that overdraw</li><li>No owner for the fail policy</li></ul></div></div>'), [
 "C: Ten mistakes. In the design: debiting at authorisation. Assuming one authorisation means one clearing record. Read, then write. Ignoring retries and early reversals. Velocity only from a stream.",
 "C: In judgment: the network gives us a hundred milliseconds. Waiting for the model, or fail open as the whole answer. Shadow mode to measure false positives. Refusing advices because they overdraw. And no owner for the fail policy."])

key("The close", "Answer in time with a <em>hold, not a debit</em>. Make every message <em>count once</em>, whatever the order. Spend the budget on what matters and <em>write down what happens when something is late</em>. And <em>record what the network decided for us</em>.", [
 "V: Answer in time with a hold, not a debit. Make every message count once, whatever the order. Spend the budget on what matters, and write down what happens when something is late. And record what the network decided for us, even when it hurts.", "[pause: 1.2]",
 "C: Thank you. I'll stop there."])
