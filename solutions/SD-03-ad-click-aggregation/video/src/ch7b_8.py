from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

# ───────── Challenge 4 · crash and replay ─────────
subchapter("7.4", "Challenge 4: Replay four hours", ["N: Challenge four is the second half of the crux: running the same thing twice."])
qs("Interviewer · challenge 4 of 6", "“You find a bug, redeploy the stream job and replay from ten o'clock, four hours back. Is anyone billed twice?”", [
 "I: You find a bug, redeploy the stream job and replay from ten o'clock, four hours back. Is anyone billed twice?", "[pause: 2.0]"])

S(dia(K(4, "a replay"), "What does a second run add to?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Flink is exactly-once.”"),
                  ("case", "Break", "The sink increments: a replay adds the same minutes on top of the first run."))), [
 P, "C: The end of the live aggregator: the window, the sink, the store, the checkpoints.", P, "C: The store sink is marked.", P,
 "C: The naive answer: Flink is exactly-once.", P,
 "C: Inside one run, it is. But if the sink adds each partial sum to what's in the store, a replay adds the same four hours on top of the first run."], cls="dia")

S(trace(K(4, "the trace"), "A fix that doubles four hours", [
  ("14:02", "a bug: reach was merged per subtask, not per campaign"),
  ("14:10", "the new build is deployed; offsets rewound to 10:00"),
  ("14:10–14:40", "minutes 10:00 – 14:00 recomputed and written again"),
  ("14:41", B("dashboards show 10:00 – 14:00 doubled; budget pacing stops 40 campaigns")),
  ("next day", B("a billing job that also adds would double the invoice"))],
  hedge=("Exactly-once inside the engine", "Checkpoints make one run see each record once. They say nothing about a second run.")), [
 "C: The trace.", P, "C: At fourteen oh two, a bug: reach was merged per subtask instead of per campaign.", P,
 "C: The fix is deployed, and the offsets rewound to ten o'clock.", P, "C: Four hours are recomputed and written again.", P,
 "C: With an adding sink, the dashboard shows those four hours doubled, and budget pacing stops forty campaigns that haven't spent anything extra.", P,
 "C: And a billing job written the same way would double the invoice.", P,
 "C: The engine's exactly-once is about one run. This question is about two."])

S(dia(K(4, "the fix"), "Replace by key and version; a second run rewrites the same rows", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "Live rows are keyed (ad, minute, shard) with a version: a newer version replaces, never adds. A billing hour is committed as a whole partition, a pure function of its manifest."),
                  ("whyb", "Covers, and does not", "Replays, restarts and re-runs with new code. It does not make a buggy run right: it makes the next run safe.")) + rejl(*REJ(4))), [
 P, "C: The fix, on the same view.", P, "C: The store sink.", P, "C: And the live store.", P,
 "C: One level down. A live row is keyed by ad, minute and shard, with a version, and ClickHouse keeps the highest version per key. So a re-emitted minute replaces the old row; it never adds. A billing hour is committed as a whole partition, a pure function of its manifest.", P,
 "C: It covers replays, restarts and re-runs with new code. It doesn't make a buggy run right. It makes the next run safe.", P,
 "C: Rejected: Flink's two-phase-commit sink on its own. It makes one run's output atomic. A second run from four hours earlier still adds on top, unless the write replaces by key."], cls="dia")

S(dia(K(4, "sequence"), "The replay, with replacing writes", "seq-ch4-replay"), [
 "C: The same replay, with replacing writes.", P, "C: On-call redeploys and rewinds to ten.", P,
 "C: Flink writes the four hours again, with higher versions.", P, "C: Same keys, higher versions: they replace, they don't add.", P,
 "C: For the bill, on-call re-runs the hour starting at ten with its manifest.", P,
 "C: The rows are identical, so the commit changes nothing. A replay is a no-op on the bill."], cls="dia")

qs("Interviewer · the second-level push", "“Finance wants last March re-run, bit for bit, two years from now.”", [
 "I: Finance wants last March re-run, bit for bit, two years from now.", "[pause: 1.5]"])

S(dia(K(4, "the second fix"), "A billing run is a pure function of its manifest", "ch4-rerun",
      extra=strip(("fixb", "Pinned inputs", "The manifest pins the events snapshot, the rate-card version, the invalidation snapshot and the image digest. The job reads no wall clock, sums integer micros and sorts before it reduces."), cols="one")), [
 P, "C: Inside the billing job.", P, "C: The hour closer, which writes the manifest.", P, "C: And the writer, which stores it beside every hour.", P,
 "C: The manifest pins four things: the events snapshot, the rate-card version, the invalidation snapshot, and the job's image digest. The job reads no wall clock, sums integer micro-dollars and sorts before it reduces. Run that image over those snapshots in two years, and March comes out bit for bit. The honest limit: raw events live six months, so after that March is reproducible from its billing rows, not from events."], cls="dia")

say_slide("“I never increment a number I can recompute. Live minutes and billing hours are written as replacements keyed by what they count, with a version, so a replay rewrites the same rows. A billing run is a pure function of a pinned manifest, which is also how I re-run March two years from now.”", [
 "V: If asked, I'd say: I never increment a number I can recompute. Live minutes and billing hours are written as replacements keyed by what they count, with a version, so a replay rewrites the same rows. A billing run is a pure function of a pinned manifest, which is also how I re-run March two years from now.", "[pause: 1.0]",
 "N: That fix creates the next question: if an hour can be re-run, what happens when its inputs change after it was billed?"])

# ───────── Challenge 5 · fraud after the invoice ─────────
subchapter("7.5", "Challenge 5: Fraud after the invoice", ["N: Challenge five: the past changes. How you record that is the grade."])
qs("Interviewer · challenge 5 of 6", "“Nine days after the invoices go out, fraud invalidates two percent of October's clicks for one advertiser. What happens?”", [
 "I: Nine days after the invoices go out, fraud invalidates two percent of October's clicks for one advertiser. What happens?", "[pause: 2.0]"])

S(dia(K(5, "a changed past"), "Edit the past, or add to it?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Delete the invalid rows and re-send the invoice.”"),
                  ("case", "Break", "The writer edits billed hours: the invoice already sent now matches nothing stored."))), [
 P, "C: Inside the billing job: the invalidations, the filter, the writer, the billing tables, invoicing.", P, "C: The writer is marked.", P,
 "C: The naive answer: delete the invalid rows and re-send the invoice.", P,
 "C: Then the writer edits hours that were billed, and the invoice already sent matches nothing we have stored."], cls="dia")

S(trace(K(5, "the trace"), "An invoice that no longer matches anything", [
  ("1 Nov", "October invoiced: advertiser A, 155 M clicks, $77.5 M"),
  ("9 Nov", "fraud flags botnet 17: 3.1 M of A's October clicks, 2 %"),
  ("9 Nov", B("naive: billed rows updated in place")),
  ("15 Nov", B("A disputes a line; no stored version matches the invoice they hold"))],
  hedge=("Two needs at once", "A credit for the invalid clicks, and an untouched record of what was invoiced.")), [
 "C: The trace.", P, "C: On the first of November, advertiser A is invoiced: a hundred and fifty-five million clicks, seventy-seven and a half million dollars.", P,
 "C: On the ninth, fraud flags botnet seventeen: three point one million of those clicks, two percent.", P,
 "C: The naive fix updates the billed rows in place.", P,
 "C: A week later A disputes a line, and we have no stored version that matches the invoice in their hand.", P,
 "C: So I need two things at once: a credit for the invalid clicks, and an untouched record of what was invoiced."])

S(dia(K(5, "the fix"), "A new version, and an adjustment line", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "Invalidations are appended with their hours; the closer marks those hours dirty and re-runs each as version n + 1; the adjuster sends v(n + 1) − invoiced as a credit line."),
                  ("whyb", "Covers, and does not", "Fraud, events past the cutoff and rate-card fixes: one path. The invoiced version stays, so every invoice line matches a stored row.")) + rejl(*REJ(5))), [
 P, "C: The fix, at the end of the billing job: the writer only ever adds a version, and the adjuster sits between it and invoicing.", P, "C: The adjuster.", P,
 "C: One level down. The fraud system appends invalidations, each with its event's hour. The closer marks those hours dirty and re-runs each as the next version, with a manifest pinning the new invalidation snapshot. Version one stays. The adjuster sends the new version minus what was invoiced as a credit line: minus one point five five million dollars.", P,
 "C: One path covers fraud, events past the cutoff, and rate-card fixes. And because the invoiced version is never touched, every invoice line still matches a stored row.", P,
 "C: Rejected: updating billed rows in place. The invoice then matches no stored version, and the audit trail ends at the edit."], cls="dia")

S(plain(K(5, "the re-run, as pseudocode"), "Dirty hours become new versions; differences become lines",
  pseudo("on invalidations(b): mark_dirty(hours(b))\nrerun(h):\n    m = manifest(h, events_snap, rates_v, invalid_snap)\n    v = latest_version(h) + 1\n    rows = price(dedup(read(h, m)) - invalid(m))\n    commit(h, v, rows, m)          # version v - 1 stays\n    for r in rows:\n        d = r.cost - invoiced(r.key)\n        if d != 0: adjustment(r.key, v, d)", hl=(3, 6, 9))), [
 "C: As pseudocode, key lines marked.",
 "C: Line three: a new manifest pins the new invalidation snapshot. Line six: the commit writes version v, and version v minus one stays. Line nine: any difference from what was invoiced becomes an adjustment.",
 "C: Why it works: a correction is the billing job with a newer manifest. There's no second code path, so a correction can't be computed differently from a bill."])

qs("Interviewer · the second-level push", "“Fraud invalidates an event from seven months ago.”", [
 "I: Fraud invalidates an event from seven months ago.", "[pause: 1.5]"])

S(plain(K(5, "the second fix, and the honest limit"), "A contract, not a mechanism", cards(
  ("amb", "Past the raw retention", "Events are kept six months; the dispute window is 90 days. Older invalidations are refused, and the refusal is logged."),
  ("grn", "Inside the window", "Any hour, any number of versions; the adjustment is always against what was invoiced."),
  ("", "Who may do it", "Only the fraud system, with a rule version on every invalidation; the manifest pins the list."), cols=3)), [
 P, "C: Seven months is past the raw retention. Events are kept six months and the dispute window is ninety days, so an older invalidation is refused, and the refusal is logged. That's a contract, not a mechanism, and I'd say so.", P,
 "C: Inside the window: any hour, any number of versions, and the adjustment is always computed against what was actually invoiced.", P,
 "C: And only the fraud system may invalidate, with a rule version on every record, so a manifest can say which rules a version used."])

say_slide("“Nothing billed is ever edited. A correction re-runs the hour as a new version, and the difference from what was invoiced becomes an adjustment line on the next invoice. The same path carries fraud, events past the cutoff and rate-card fixes, so every invoice still matches a stored version.”", [
 "V: If asked, I'd say: nothing billed is ever edited. A correction re-runs the hour as a new version, and the difference from what was invoiced becomes an adjustment line on the next invoice. The same path carries fraud, events past the cutoff and rate-card fixes, so every invoice still matches a stored version.", "[pause: 1.0]",
 "N: That fix creates the last question. Every part can now be right. How would you know when one of them isn't?"])

# ───────── Challenge 6 · observability ─────────
subchapter("7.6", "Challenge 6: “Your numbers are 3 % high”", ["N: Challenge six is observability, and in this question it is about a wrong number, not a down server."])
qs("Interviewer · challenge 6 of 6", "“An advertiser says our clicks are three percent higher than their own logs. What do you do, and how would you have known first?”", [
 "I: An advertiser says our clicks are three percent higher than their own logs. What do you do, and how would you have known first?", "[pause: 2.0]"])

S(dia(K(6, "a wrong number"), "Who would have noticed?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Lag, CPU and error rate are all green.”"),
                  ("case", "Break", "Every container healthy; the number at the reporting API wrong."))), [
 P, "C: Back to the container view, version three.", P, "C: The reporting A-P-I is marked: that's where the advertiser sees the number.", P,
 "C: The naive answer: lag, C-P-U and error rate are all green.", P,
 "C: And they are. Every container is healthy, and the number is wrong."], cls="dia")

S(trace(K(6, "the trace"), "A units typo, three days of green", [
  ("Mon 09:00", "a config push sets the dedup lifetime to 10 seconds instead of 10 minutes"),
  ("Mon 09:00 →", "lag, CPU, errors: green; live clicks 3 % above their usual ratio to impressions"),
  ("Wed 09:00", "Monday's final hours are right: the billing run dedups the whole hour"),
  ("Thu", B("an advertiser compares live screenshots with their logs: +3 %"))],
  hedge=("What the dashboards saw", "Nothing. Every system was healthy; one number was wrong for three days.")), [
 "C: The trace.", P, "C: Monday at nine, a config push sets the dedup lifetime to ten seconds instead of ten minutes. A units typo.", P,
 "C: Lag, C-P-U and errors stay green. Live clicks run three percent above their usual ratio to impressions, and nothing watches that.", P,
 "C: On Wednesday Monday's final hours are right, because the billing run deduplicates the whole hour.", P,
 "C: On Thursday an advertiser compares their screenshots with their logs and calls.", P,
 "C: Every system was healthy. One number was wrong for three days."])

S(dia(K(6, "the fix"), "Version four: a reconciler that checks numbers, not machines", "base-v4", vtag="V4"), [
 P, "C: The fix changes the design, so this is version four. Version three, carried.", P,
 "C: New: a reconciler. It reads the collectors' accepted counts and the live store, where the final hours also land."], cls="dia")

S(plain(K(6, "the fix, one level down"), "Three checks on the numbers, and a trail for every line", cards(
  ("grn", "Conservation per hop", "Per minute: accepted = appended = landed − duplicates."),
  ("grn", "Live against final", "Every closed hour, per campaign: alert above 0.5 %."),
  ("grn", "Canaries", "Events with known IDs every minute: exactly once in both."), cols=3) +
  strip(("whyb", "Answering the advertiser", "Invoice line → hour version → manifest → the event IDs, exportable for their line."), cols="one") + rejl(*REJ(6))), [
 "C: One level down, three checks on the numbers themselves.", P,
 "C: Conservation at every hop, per minute: accepted equals appended equals landed, minus duplicates.", P,
 "C: Live against final for every closed hour, alerting above half a percent. That one would have fired on Wednesday.", P,
 "C: And canary events with known I-Ds every minute, each expected exactly once in the live store and in the final hour.", P,
 "C: And to answer the advertiser: the invoice line points to an hour version, the version to its manifest, the manifest to the event I-Ds. We can export the I-Ds behind their line and compare.", P,
 "C: Rejected: lag and C-P-U dashboards. They stay green while the pipeline counts wrong. Only conservation checks and canaries see a wrong number."])

S(plain(K(6, "reading the signals"), "Symptoms in pairs: what each one means", table(["Symptom", "Paired with", "Means"], [
  ["Live clicks up 3 %", "final for the same hour flat", "duplicates on the live path"],
  ["Live and final both up", "impressions up too", "real traffic"],
  ["Accepted above landed", "log lag flat", "the lake sink is losing files"],
  ["A canary seen twice", "—", "a duplicate path, wherever it is"],
  ["Clamped share above 0.1 %", "one SDK version", "a client clock bug"]], "bt sm")), [
 "C: One more habit: read symptoms in pairs. A number alone is not a diagnosis.", P,
 "C: Live clicks up three percent while the final for the same hour is flat: duplicates on the live path. Our case.", P,
 "C: Live and final both up, with impressions up too: real traffic. Nobody gets paged.", P,
 "C: Accepted above landed, while log lag is flat: the lake sink is losing files.", P,
 "C: A canary seen twice: a duplicate path, wherever it is.", P,
 "C: And a clamped share above a tenth of a percent, all from one S-D-K version: a client clock bug."])

qs("Interviewer · the second-level push", "“And if the reconciler itself is wrong?”", [
 "I: And if the reconciler itself is wrong?", "[pause: 1.5]"])

S(plain(K(6, "the second fix"), "Check the checker", cards(
  ("grn", "Canaries check the checker", "A known number of canaries a minute: the reconciler must count exactly that many, or it pages about itself."),
  ("amb", "Silence is a failure", "No comparison for 15 minutes pages: an alert that cannot fire is not an alert."), cols=2)), [
 P, "C: The canaries check the checker. A known number of them a minute, so the reconciler must count exactly that many, or it pages about itself.", P,
 "C: And silence is a failure. If no comparison has run for fifteen minutes, that pages too. An alert that cannot fire is not an alert."])

say_slide("“I'd answer the advertiser with the event IDs behind their line: invoice line, hour version, manifest, events. And I'd want to have seen it first: conservation at every hop, live against final every hour, and canary events whose count I know, so a wrong number pages even when every system is healthy.”", [
 "V: If asked, I'd say: I'd answer the advertiser with the event I-Ds behind their line: invoice line, hour version, manifest, events. And I'd want to have seen it first: conservation at every hop, live against final every hour, and canary events whose count I know, so a wrong number pages even when every system is healthy.", "[pause: 1.0]"])

# ───────────────────────── 8 · recap ─────────────────────────
chapter(8, "Recap", 6, "The final design, and what to say", [
 "C: The recap. One picture, the mechanisms on it, and the mistakes that cost most."])

S(dia("Recap · version four", "Where each mechanism ended up", "recap"), [
 P, "C: Version four, the final design. The same picture as version one, with four boxes more. The labels from the theory chapter come back on it.", P,
 "C: The collector keeps the I-D the S-D-K minted. It never makes one up.", P,
 "C: The live aggregator runs four of the five mechanisms: the I-D, event time, two-stage sums and the reach sketches. Record, then live, within ten seconds.", P,
 "C: The live store replaces by version. It never increments.", P,
 "C: The billing job runs the same code at the close, over a pinned snapshot: the I-D, event time and replacement.", P,
 "C: The billing tables hold versions, so a correction is a new row and an adjustment, never an edit.", P,
 "C: And the reconciler checks the numbers themselves, with canaries whose count it knows."], cls="dia")

S(plain("Recap · the mistakes", "What costs most in this round", table(["Mistake", "Instead"], [
  ["<code>n = n + 1</code> per event, in a database", "a log first; counts derived from it"],
  ["“Exactly-once” said as a name", "at-least-once plus dedup on an ID minted at the source"],
  ["Counting by arrival time", "event time, clamped; a watermark; a cutoff"],
  ["One run for the dashboard and the bill", "one code, run twice: provisional, then final"],
  ["Editing billed rows", "versions and adjustment lines"],
  ["No way to show the events behind a line", "a manifest per hour; canaries; conservation checks"]], "bt sm")), [
 "N: The mistakes that cost most in this round.", P,
 "N: n equals n plus one, per event, in a database. Instead, a log first, and counts derived from it.", P,
 "N: Exactly-once said as a name. Instead, at-least-once plus dedup on an I-D minted at the source.", P,
 "N: Counting by arrival time. Instead, event time, clamped, with a watermark and a cutoff.", P,
 "N: One run for both the dashboard and the bill. Instead, one code, run twice.", P,
 "N: Editing billed rows. Instead, versions and adjustment lines.", P,
 "N: And no way to show the events behind an invoice line. Instead, a manifest per hour, canaries and conservation checks."])

key("The close", "Count once, from <em>one log</em>, with <em>one piece of code run twice</em>. Never increment what you can recompute: <em>replace</em> it, and keep every version you billed.", [
 "V: Count once, from one log, with one piece of code run twice. Never increment what you can recompute. Replace it, and keep every version you billed.", "[pause: 1.0]",
 "C: Thanks for watching. The written design, with every number and the internals of each tool, is linked below."])
