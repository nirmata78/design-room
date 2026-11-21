from dsl import *

K = lambda n, t: f"Challenge {n} of 8 · {t}"

# ───────── Challenge 5 · explain a decision ─────────
subchapter("7.5", "Challenge 5: Explain a decision fourteen months later", ["N: Challenge five. A regulator asks why a customer was declined more than a year ago: can we show what we knew, and what we decided, then?"])
qs("Interviewer · challenge 5 of 8", "“A regulator asks why a customer was declined fourteen months ago. Reproduce it.”", [
 "I: A regulator asks why a customer was declined fourteen months ago. Reproduce it.", "[pause: 2.0]"])

S(dia(K(5, "explain it later"), "The policy engine only knows today", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Re-run the model on the customer's data.”"),
                  ("case", "Break", "The policy engine: today's model, today's rules, today's credit file."))), [
 "C: The naive answer: re-run the model on the customer's data. The red box is the policy engine, and it only knows today: today's model, today's rules, and today's credit file."], cls="dia")

S(plain(K(5, "the trace"), "A notice that says one thing, a replay that says another", '<pre class="trace"><span class="t">Jan 2026</span>ap_204 declined by model v9, policy v31\n<span class="t">Jan 2026</span>notice sent: “high utilisation, short history”\n<span class="t">2026</span>models v10 to v14 ship; policy reaches v38\n<span class="t">Mar 2027</span>regulator: why was ap_204 declined?\n<span class="t">Mar 2027</span>re-run v14 on today\'s bureau file: <span class="bad">APPROVE</span>\n<span class="t">so</span><span class="bad">the notice and the replay disagree, and neither shows what happened</span></pre>', q=True, red=True), [
 "C: The trace. In January twenty twenty-six, application two-oh-four is declined by model version nine under policy thirty-one, and the customer is sent a notice: high utilisation, short history. During the year, five model versions ship. In March twenty twenty-seven the regulator asks why. Someone re-runs today's model on today's credit file, and it approves.",
 "C: Now we hold a notice that says one thing and a replay that says another, and neither shows the regulator what actually happened."])

S(dia(K(5, "the fix"), "Write down what we knew, once", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "An immutable decision record written by the orchestrator: frozen inputs, every version, the outputs with ranked reasons. Old models stay loadable. A nightly replay of a sample."),
                  ("whyb", "Property", "S2: the same inputs and versions give the same answer, and the replay proves it every night, not on the day the regulator asks."))), [
 "C: The fix: an immutable decision record, outlined green, written once by the orchestrator for every decision. Old model artefacts stay loadable in a registry. And a replay job runs every night on a sample of records and alarms on any difference. S-two: the same inputs and the same versions give the same answer, and we prove it every night rather than on the day we're asked."], cls="dia")

S(dia(K(5, "what a record holds"), "Inputs, versions, outputs", "record"), [
 "C: What a record holds. Inputs, frozen: the bureau report stored encrypted and referenced, the identity and fraud results, our own history as of that moment, the exact feature vector, and which calls were missing. Versions: model, policy including the missing-data table, pricing, disclosure, and the orchestrator build.",
 "C: Outputs: the outcome and offers, the ranked reasons, the degraded path taken, the timings, and who signed the policy. About fifty kilobytes, written once."], cls="dia")

S(dia(K(5, "sequence"), "The replay matches the notice", "seq-ch5-replay"), [
 "C: The replay as a sequence. The request: explain two-oh-four from January. Load the record: the features, the report reference, model nine, policy thirty-one. Load those versions from the registry. Re-score the frozen features. Decline: high utilisation, short history. It matches the notice, because it is what we knew and how we decided then."], cls="dia")

qs("Interviewer · the second-level push", "“The customer asks us to delete their data. The record holds their bureau report.”", [
 "I: The customer asks us to delete their data. The record holds their bureau report.", "[pause: 2.0]"])

S(plain(K(5, "the second fix, and the honest limit"), "Retention wins for its period; then destroy the key", '<div class="cards c3">'
  '<div class="cd"><h3>Who decides</h3><p>Retention duties for credit records take precedence for their period. Compliance owns that call, not engineering.</p></div>'
  '<div class="cd grn"><h3>Within the period</h3><p>Tokens, not identity; the report encrypted under a key per record; use restricted to allowed purposes.</p></div>'
  '<div class="cd amb"><h3>At the end</h3><p>Destroy the record\'s key: every copy, backups included, becomes unreadable at once.</p></div></div>' +
  line("Honest limit: a deletion request inside the retention period is answered by restricting use, and the customer is told so.", "r")), [
 "C: Who decides comes first. Retention duties for credit records generally take precedence for their period, and that call belongs to compliance, not engineering. Within the period, the record holds tokens rather than identity, and the report is encrypted under a key per record, with use restricted to the purposes the rules allow.",
 "C: At the end of retention we destroy the record's key. That makes every copy unreadable at once, backups included, without hunting for them. That's called crypto-shredding. The honest limit: a deletion request inside the period is answered by restricting use, and the customer is told so."])

say_slide("“I never re-run today's model to explain yesterday. Every decision freezes its inputs, versions and ranked reasons, and a nightly replay proves records still reproduce.”", [
 "V: If asked, I'd say: I never re-run today's model to explain yesterday. Every decision freezes its inputs, versions and reasons, and a nightly replay proves they still reproduce.", "[pause: 1.0]",
 "N: Records make the past safe. The next question changes the future: a new model."])

# ───────── Challenge 6 · a new model ─────────
subchapter("7.6", "Challenge 6: A new model approves six percent more", ["N: Challenge six. Data science has a model that approves more people: how do we learn whether they repay without betting a hundred million dollars?"])
qs("Interviewer · challenge 6 of 8", "“Data science has a new model. It approves six percent more people at the same predicted loss. Roll it out.”", [
 "I: Data science has a new model. It approves six percent more people at the same predicted loss. Roll it out.", "[pause: 2.0]"])

S(dia(K(6, "a new model"), "Where a new model's risk lands", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Shadow mode for a week, it looks good, switch it on.” Or: “a fifty-fifty A/B test.”"),
                  ("case", "Break", "The policy engine: a switch that changes a hundred million dollars of exposure a month."))), [
 "C: The naive answers: shadow mode for a week, it looks good, switch it on. Or a fifty-fifty test. The red box is the policy engine, and a switch there changes about a hundred million dollars of exposure a month."], cls="dia")

S(plain(K(6, "the trace"), "Approvals today, losses in four months", '<pre class="trace"><span class="t">month 0</span>6 % of 2 million = 120,000 more approvals a month\n<span class="t">month 0</span>× 70 % take-up ≈ 84,000 more loans ≈ <span class="bad">$100M a month of new exposure</span>\n<span class="t">weeks 2–4</span>first payments fall due\n<span class="t">days 90–120</span>losses become visible\n<span class="t">after a week</span><span class="bad">shadow shows the approval rate, and nothing about repayment</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Derived from the given volume; take-up and loss timing are illustrative.</div>', q=True, red=True), [
 "C: The trace. Six percent of two million is a hundred and twenty thousand more approvals a month. At seventy percent take-up, about eighty-four thousand more loans, about a hundred million dollars a month of new exposure. The first payments fall due in two to four weeks, and losses only become visible at ninety to a hundred and twenty days.",
 "C: A week of shadow shows the approval rate. It shows nothing about whether the newly approved people repay. And a fifty-fifty test bets fifty million a month to find out."])

S(dia(K(6, "the fix"), "A challenger beside the champion, capped", "ch6-fix",
      extra=strip(("fixb", "Mechanism", "Backtest → shadow → a 5 % challenger slice under its own exposure cap → early signals at 30–45 days → widen by a policy version change, with a kill switch."),
                  ("whyb", "Property", "S2 kept: every record says which model decided. The cost of learning is bounded by the slice cap, not by optimism."))), [
 "C: The fix: champion and challenger, outlined green. The challenger sits beside the champion, and decides only a capped slice. Every record says which model decided, so S-two holds, and the cost of learning is bounded by the cap."], cls="dia")

S(dia(K(6, "the steps"), "Each step sees what the one before cannot", "rollout"), [
 "C: The steps. A backtest on labelled history. Then shadow: both models score every application, the champion acts, and we compare approval rates and reasons by segment and by protected group. Then a challenger slice: five percent of traffic, under its own cap. Five percent of the extra approvals is about six thousand a month, four thousand two hundred loans, about five million dollars, signed by credit risk and the partner bank.",
 "C: Then early signals at thirty to forty-five days: a first payment missed, compared between similar people approved by each model. And widening only through a policy version change, with a kill switch per version."], cls="dia")

qs("Interviewer · the second-level push", "“Shadow looked great. Why isn't that enough?”", [
 "I: Shadow looked great. Why isn't that enough?", "[pause: 2.0]"])

S(plain(K(6, "the second fix, and the honest limit"), "Shadow cannot see loss", '<div class="cards c3">'
  '<div class="cd red"><h3>No labels</h3><p>People only the challenger would approve were declined by the champion. They never got a loan, so there is no repayment to observe.</p></div>'
  '<div class="cd grn"><h3>Only a slice learns</h3><p>Only where the challenger decides do those people get loans, and labels.</p></div>'
  '<div class="cd"><h3>Fairness, twice</h3><p>On shadow: who would be approved. On the slice: who repays. Thresholds owned by compliance.</p></div></div>' +
  line("Honest limit: a slice is real money at risk. The cap is the price of learning, and credit risk owns it.", "r")), [
 "C: Because shadow cannot see loss. The people only the challenger would approve were declined by the champion. They never got a loan, so there's no repayment to observe. Only a slice where the challenger actually decides gives them loans, and gives us labels. Fairness checks run twice: on shadow, for who would be approved, and on the slice, for who repays.",
 "C: The honest limit: a slice is real money at risk. The cap is the price of learning, and credit risk owns that price."])

say_slide("“Shadow tells you who the new model would approve, not whether they repay. So: backtest, shadow, a capped slice where the challenger decides, early signals at thirty days, and a kill switch.”", [
 "V: If asked, I'd say: shadow tells you who a new model would approve, not whether they repay. So: backtest, shadow, a capped slice, early signals at thirty days, and a kill switch.", "[pause: 1.0]",
 "N: Training the next model needs data. Which data is the next question."])

# ───────── Challenge 7 · identity ─────────
subchapter("7.7", "Challenge 7: Where identity data lives", ["N: Challenge seven. Analytics wants the application data to train a model: what do they get, and where does identity actually live?"])
qs("Interviewer · challenge 7 of 8", "“The analytics team wants application data to train the next model. What do they get?”", [
 "I: The analytics team wants application data to train the next model. What do they get?", "[pause: 2.0]"])

S(dia(K(7, "identity"), "Identity in rows, logs and exports", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“A copy of the database; we encrypt it at rest.” Or: “we drop the name column.”"),
                  ("case", "Break", "The application service, its database and the export: identity everywhere they go."))), [
 "C: The naive answers: give them a copy of the database, it's encrypted at rest. Or drop the name column. The red boxes are the application service, its database, and the export to analytics, and identity goes wherever they go."], cls="dia")

S(plain(K(7, "the trace"), "One extract, two million identities", '<pre class="trace"><span class="t">table</span>application holds SSN, date of birth, address\n<span class="t">log</span>the bureau adapter\'s debug line prints the full request\n<span class="t">support</span>every agent sees the full number\n<span class="t">extract</span>names dropped; <span class="bad">date of birth + postcode re-identify most people</span>\n<span class="t">a leak</span><span class="bad">one extract = two million identities a month</span></pre>' +
  '<div class="hedge"><b class="t">Encryption at rest</b>Protects a stolen disk. Does nothing for a query, a log line or an export.</div>', q=True, red=True), [
 "C: The trace, in version two. The application table holds the social security number, the date of birth and the address. The bureau adapter's debug log prints the full request. Every support agent sees the full number. The training extract drops names but keeps date of birth and postcode, which together re-identify most people. One leaked extract is two million identities a month.",
 "C: And encryption at rest protects a stolen disk. It does nothing for a query, a log line or an export."])

S(dia(K(7, "the fix"), "Only two things see real values", "ch7-fix",
      extra=strip(("fixb", "Mechanism", "A vault: identity tokenised at apply; only the vault and the vendor adapters detokenise; every access logged with a purpose; logs scrubbed at the adapter. Training gets derived features."),
                  ("whyb", "Property", "S3 by construction: a leak anywhere outside the boundary leaks tokens."))), [
 "C: The fix: an identity vault, outlined green. Identity is tokenised at apply. Only two things sit inside the boundary: the vault, and the vendor adapters, which must send real values to the bureau. Every detokenise is logged with its caller and purpose, and adapter logs are scrubbed at the source. So analytics gets tokens and derived features, like utilisation and history length, never identity. S-three, by construction."], cls="dia")

S(dia(K(7, "the boundary"), "Drawn small on purpose", "vault"), [
 "C: The boundary, drawn small on purpose. Inside: the vault with keys per field, and the adapters. Outside, everything else: the application service and database, decision records, support tools with masked values, and analytics with features. They all carry tokens.",
 "C: And know the rulebook, because interviewers test it. Card numbers fall under the card industry's security standard. A social security number doesn't: it falls under privacy and lending law."], cls="dia")

qs("Interviewer · the second-level push", "“The vault is down.”", [
 "I: The vault is down.", "[pause: 2.0]"])

S(plain(K(7, "the second fix, and the honest limit"), "Tier zero, and boring on purpose", '<div class="cards c3">'
  '<div class="cd grn"><h3>Small and replicated</h3><p>No business logic. Replicated across zones. Its own 99.95 % objective and its own on-call.</p></div>'
  '<div class="cd amb"><h3>When it is down</h3><p>Nothing new starts: applications refer, the merchant sees pending. Booked loans continue.</p></div>'
  '<div class="cd red"><h3>Never “help” it</h3><p>Nothing raw is ever cached outside the vault to ride out an outage.</p></div></div>' +
  line("Honest limit: the vault is reliable because it is small. Resist every feature request that would grow it.", "r")), [
 "C: The vault is a tier-zero dependency, so it's kept small, with no business logic, replicated across zones, with its own objective of ninety-nine point nine five percent and its own on-call. When it's down, nothing new can start: applications refer, and the merchant sees pending. Loans already booked carry on. And nothing raw is ever cached outside it to help.",
 "C: The honest limit: the vault is reliable because it is small. Resist every feature request that would grow it."])

say_slide("“They get tokens and derived features, never identity. Only the vault and the vendor adapters see real values, every access is logged, and identity data falls under privacy and lending law, not the card standard.”", [
 "V: If asked, I'd say: analytics gets tokens and features, never identity. Only the vault and the adapters see real values, and every access is logged.", "[pause: 1.0]",
 "N: Last challenge: with all of this in place, how would we know it is broken?"])

# ───────── Challenge 8 · observability ─────────
subchapter("7.8", "Challenge 8: How would you know it is broken?", ["N: Challenge eight. The dashboards are green: how would we know decisions are going wrong, before merchants tell us?"])
qs("Interviewer · challenge 8 of 8", "“Your dashboards are green. How would you know decisions are going wrong?”", [
 "I: Your dashboards are green. How would you know decisions are going wrong?", "[pause: 2.0]"])

S(dia(K(8, "a silent failure"), "No error, no latency, wrong answers", "ch8-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Error rate, latency and CPU.”"),
                  ("case", "Break", "The policy engine: a change that returns valid, wrong decisions."))), [
 "C: The naive answer: error rate, latency and CPU. The red box is the policy engine, which can return perfectly valid, perfectly wrong decisions."], cls="dia")

S(plain(K(8, "the trace"), "Fifteen hours of wrong declines", '<pre class="trace"><span class="t">Fri 18:00</span>a pricing-table change maps one bureau field wrongly\n<span class="t">18:00</span>no errors · latency fine · CPU flat\n<span class="t">18:00</span><span class="bad">approval rate, all merchants: 62 % → 41 %</span>\n<span class="t">per hour</span>about 2/s × 3,600 = 7,200; <span class="bad">≈ 1,500 wrongly declined, each with a notice</span>\n<span class="t">Sat 09:00</span>merchants start calling: <span class="bad">≈ 22,000 customers</span></pre>' +
  '<div class="hedge"><b class="t">Label the numbers</b>Illustrative, assuming the evening rate held overnight.</div>', q=True, red=True), [
 "C: The trace. At six on Friday evening, a pricing-table change maps one bureau field wrongly. No errors, latency fine, C-P-U flat. The approval rate across all merchants drops from sixty-two to forty-one percent. At about two applications a second, that's seven thousand two hundred an hour, about fifteen hundred wrongly declined every hour, each with a notice.",
 "C: It's found at nine on Saturday morning, when merchants start calling. About twenty-two thousand customers, if the evening rate held."])

S(dia(K(8, "the fix"), "Watch the decision, not the servers", "ch8-fix",
      extra=strip(("fixb", "Mechanism", "SLIs on the promise and on the decision; read in pairs. Policy and pricing changes ship as canaries on a small slice with the approval-rate alarm armed."),
                  ("whyb", "Property", "The SLIs measure what the customer and the lender experience; a pair of metrics turns into one cause."))), [
 "C: The fix: measure the decision, not the servers, outlined green across the orchestrator, the policy engine and funding. And ship every policy and pricing change as a canary on a small slice, with the approval-rate alarm armed. This change would have been caught in minutes, on a few hundred applications."], cls="dia")

S(plain(K(8, "the signals"), "What pages, and why", table(["SLI", "Why it pages"], [
  ["Offers on screen within 3 s, p95", "The promise at the counter"],
  ["Approval rate per merchant per hour, against its baseline", "A sudden drop is almost never the customers"],
  ["Fallback rate per policy row, against its cap", "Credit risk said “capped”: prove it"],
  ["Loans booked and not funded after an hour, batch-aware", "Money owed to a merchant"],
  ["Vendor errors, latency and spend per hour", "The deadline's enemy and the largest cost"],
  ["The mix of decline reasons", "A new dominant reason is a change, not a population"]], "bt sm")), [
 "C: Six signals. Offers within three seconds: the promise itself. Approval rate per merchant per hour against its own baseline: a sudden drop is almost never the customers. The fallback rate per policy row against its cap, because credit risk was promised a cap. Loans booked and not funded, which is money owed. Vendor errors, latency and spend. And the mix of decline reasons: a new dominant reason is a change, not a population."])

S(plain(K(8, "symptom pairs"), "Two metrics, one cause", table(["When you see", "Together with", "It means"], [
  ["Approval down", "vendor errors flat, a deploy at the same time", "our change"],
  ["Refer rate up", "a breaker open", "an outage, handled as designed"],
  ["Offer latency up", "breakers closed", "a vendor slow, under the breaker's threshold"],
  ["Booked up", "funded flat", "funding stuck"],
  ["One decline reason jumps", "one bureau's field distribution shifted", "a vendor changed a field"]], "bt sm")), [
 "C: Then read them in pairs. Approval down with vendor errors flat and a deploy at the same time: our change. Refer rate up with a breaker open: an outage being handled as designed. Offer latency up with breakers closed: a vendor slow, but under the threshold. Booked up and funded flat: funding stuck. And one decline reason jumping while one bureau's fields shift: the vendor changed a field."])

qs("Interviewer · the second-level push", "“Approval drops at one merchant only.”", [
 "I: Approval drops at one merchant only.", "[pause: 2.0]"])

S(plain(K(8, "the second fix, and the honest limit"), "One merchant is usually not credit", '<div class="cards c3">'
  '<div class="cd"><h3>Baselines</h3><p>Per merchant, by hour of the week.</p></div>'
  '<div class="cd amb"><h3>Usual causes</h3><p>An integration bug (amounts in dollars, not cents), or a fraud ring testing stolen identities.</p></div>'
  '<div class="cd grn"><h3>Route it</h3><p>To merchant operations or fraud, not to credit risk.</p></div></div>' +
  line("Honest limit: small merchants have noisy baselines. Alarm on totals over a window, not on one hour.", "r")), [
 "C: Per-merchant baselines, by hour of the week. A drop at one merchant is usually an integration bug, like amounts sent in dollars instead of cents, or a fraud ring testing stolen identities. So it goes to merchant operations or fraud, not to credit risk.",
 "C: The honest limit: small merchants have noisy baselines. Alarm on totals over a window, not on a single hour."])

say_slide("“I watch the decision, not the servers: offers in three seconds, approval per merchant per hour, fallback against its cap, booked but not funded. Two metrics together tell me whether it's us, a vendor or one merchant.”", [
 "V: If asked, I'd say: I watch the decision, not the servers. Offers in three seconds, approval per merchant, fallback against its cap, and two metrics together for the cause.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost ─────────────────────────
chapter(8, "Build cost", 6, "Who, how long, buy or build: the manager layer", [
 "C: Build cost. This is the manager layer, marked aux: skip it in a pure Staff round, use it in a manager round."], aux=True)

S(plain("Build cost · releases", "Three versions, three budgets", table(["", "V1", "V2", "V3"], [
  ["Scope", "one service, sequential calls, one table", "orchestrator, state machine, outbox, policy engine", "vault, records, policy table, funding, challenger"],
  ["People", "3 engineers", "a team of 6", "two teams, plus security and compliance time"],
  ["Time", "2 months, to learn the vendors", "2 quarters", "2 more quarters"],
  ["Riskiest first", "vendor adapters", "the policy table", "funding and reconciliation"]], "bt sm")), [
 "C: Three releases. Version one, sequential calls and one table: three engineers, two months, mostly to learn the vendors. Version two, the orchestrator, state machine, outbox and policy engine: a team of six for two quarters. Version three, the vault, records, policy table, funding and the challenger: two teams for two more quarters, plus security and compliance time. Riskiest work first: the vendor adapters and the policy table, because they decide whether the counter promise holds."], cls="aux")

S(dia("Build cost · team seams", "Six owners, three contracts", "teams"), [
 "C: Six owners. Applications and origination own the state machine and booking. The decisioning platform owns the orchestrator, the policy engine and serving. Vendor integrations own the adapters, contracts and spend. Security owns the vault. Credit risk and data science own the models and every degraded path. Compliance owns disclosures, notices and retention.",
 "C: The contracts between them are three: the decision interface, the decision record, and the loan booked event."], cls="dia aux")

S(plain("Build cost · buy or build", "Buy what is not the decision", '<div class="cards c3">'
  '<div class="cd"><h3>Buy</h3><p>Bureaus, identity and bank data. A tokenisation vault is a reasonable buy. A workflow engine, if steps grow to days.</p></div>'
  '<div class="cd grn"><h3>Build</h3><p>The orchestrator, the policy engine, the records: a regulator asks us, not a vendor, why someone was declined.</p></div>'
  '<div class="cd amb"><h3>Half the team</h3><p>Keep deadline, policy table, atomic booking, records. Buy the vault. Defer the challenger and bank data.</p></div></div>'), [
 "C: Buy, build, or defer. Buy the data: bureaus, identity and bank data, and a tokenisation vault is a reasonable buy. Build what is the decision: the orchestrator, the policy engine and the records, because a regulator asks us, not a vendor, why someone was declined. With half the team, keep the deadline, the policy table, the atomic booking and the records, buy the vault, and defer the challenger and bank data."], cls="aux")

S(plain("Build cost · money and risks", "The bill, and what could sink it", '<div class="cards c2">'
  '<div class="cd"><h3>The bill (illustrative)</h3><p>Bureau pulls about $2M a month; identity about $100k; compute and storage a small fraction. Levers: report reuse, no races, pull only when the policy needs it.</p></div>'
  '<div class="cd red"><h3>Top risks</h3><p>A degraded path without an owner or a cap. A model change without a replayable record. Identity leaking into logs. Funding retries without an UNKNOWN state.</p></div></div>'), [
 "C: The bill, illustrative: bureau pulls about two million a month, identity about a hundred thousand, compute a small fraction. The levers are report reuse, no races, and pulling only when the policy needs it.",
 "C: The top risks: a degraded path without an owner or a cap. A model change without a replayable record. Identity leaking into logs. And funding retries without an unknown state."], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, four paths, the mistakes, the thesis", [
 "C: The recap: one picture, a sentence per path, the common mistakes, and the thesis."])

S(dia("Recap · the final design", "One picture", "base-final"), [
 "C: The whole design. Across the middle, the counter path: phone, edge, application service, orchestrator, vendors. Above, the vault. Below, what happens after booking, and what we keep: the database with its outbox, the event log, funding, the policy engine and the decision records."], cls="dia")

S(plain("Recap · four paths", "One sentence each", table(["Path", "In one sentence", "Serves"], [
  ["Apply", "Tokenise, create the row, answer at once with an ID", "FR1 · S3"],
  ["Decide", "All vendors at once, one deadline, a signed policy for what's missing, a record", "FR2 · L1 S2 S4"],
  ["Book", "One transaction: conditional update, unique loan, outbox row", "FR3 · S1"],
  ["Fund", "Its own state machine, UNKNOWN as a state, reconciled daily", "FR4 · L2"]], "bt sm")), [
 "C: Apply: tokenise, create the row, answer at once. Decide: all vendors at once, one deadline, a signed policy for whatever is missing, and a record. Book: one transaction, a conditional update, a unique loan and the outbox row. Fund: its own state machine, with unknown as a state, reconciled every day."])

S(plain("Recap · how it degrades", "In priority order: what still works", table(["What fails", "What still works", "The customer sees"], [
  ["One bureau slow", "everything; the deadline decides", "offers, rarely a refer"],
  ["One bureau down", "second bureau, small known customers, refer", "offers, or “we'll text you”"],
  ["Policy engine down", "apply still records; nothing decides", "pending; the refer queue fills"],
  ["Vault down", "nothing new starts; booked loans continue", "pending"],
  ["Event log or funding down", "booking continues; the outbox holds events", "nothing; merchants paid in the next batch"]], "bt sm")), [
 "C: How it degrades, in priority order. A slow bureau changes nothing: the deadline decides. A bureau down uses the table: second bureau, small known customers, refer. If the policy engine is down, applications are still recorded, and they wait in the refer queue. If the vault is down, nothing new starts, but booked loans carry on.",
 "C: And if the event log or funding is down, the counter doesn't notice at all: booking continues, the outbox holds the events, and merchants are paid in the next batch. The customer at the counter is protected first, the merchant's money second, and everything else can wait."])

S(plain("Recap · common mistakes", "What costs points in this round", '<div class="cards c2">'
  '<div class="cd red"><h3>Design</h3><p>Treating it as a throughput problem. Sequential vendor calls. Hedging paid pulls. A saga that compensates a credit pull. Check-then-insert on the loan.</p></div>'
  '<div class="cd amb"><h3>Judgement</h3><p>“Approve with partial data” as a default. Re-running today\'s model to explain yesterday. “Encrypt the database” for identity. The card standard quoted for an SSN. No owner for any degraded path.</p></div></div>'), [
 "N: The mistakes that cost points. In the design: treating it as a throughput problem, sequential calls, hedging paid pulls, a saga that compensates a credit pull, and check-then-insert on the loan.",
 "N: In judgement: approve with partial data as a default, re-running today's model to explain yesterday, encrypt the database as the identity answer, the card standard quoted for identity data, and no owner for any degraded path."])

key("The close", "The core is small and boring on purpose: <em>one database, one atomic step</em>. The design lives at the slow edges and in what we keep: <em>one deadline</em> with a signed policy, a record that <em>replays</em>, identity in a <em>vault</em>.", [
 "V: The core is small and boring on purpose. The design lives at the slow edges and in what we keep: one deadline with a signed policy, a record that replays, and identity in a vault.", "[pause: 1.2]"])
