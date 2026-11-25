from dsl import *

K = lambda n, t: f"Challenge {n} of 7 · {t}"

# ───────── Challenge 5 · hostile URLs and forged calls ─────────
subchapter("7.5", "Challenge 5: Hostile URLs and forged calls", ["N: Challenge five. Self-service URLs are input that our servers will call, and a webhook that releases goods is worth forging."])
qs("Interviewer · challenge 5 of 7", "“Someone registers http://169.254.169.254/ as their webhook URL. Someone else POSTs a fake loan.approved to a merchant's till. Go.”", [
 "I: Someone registers one-six-nine, two-five-four, one-six-nine, two-five-four as their webhook U-R-L. Someone else POSTs a fake loan approved event to a merchant's till. Go.", "[pause: 2.0]"])

S(dia(K(5, "trust the input"), "A URL check and a shared header", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Validate the URL at registration; send an API key in a header.”"), cols="one")), [
 "C: The naive answer: validate the U-R-L at registration, and send an A-P-I key in a header so the till knows it's us. The H-T-T-P client and the path out, marked red, trust what they were given."], cls="dia")

S(trace(K(5, "the trace"), "Our own credentials, and a free television", [
  ("Mon 10:00", "hooks.attacker.example registered: it resolves to 203.0.113.5, check passed"),
  ("Mon 10:05", "<span class='bad'>at send time it resolves to 169.254.169.254: we POST to the cloud metadata service</span>"),
  ("Mon 10:05", "<span class='bad'>the answer's first bytes, a credential, are shown in the attacker's delivery log</span>"),
  ("Mon 11:00", "a fraudster POSTs loan.approved, $2,400, to a till's public URL with a copied header"),
  ("Mon 11:01", "<span class='bad'>the till releases a television; no such loan exists</span>")]), [
 "C: The trace.", "[+]", "C: A name is registered that resolves to a public address. The check passes.",
 "[+]", "C: At send time the name resolves to the cloud's metadata address, and our dispatcher POSTs to it from inside our network.",
 "[+]", "C: The first bytes of the answer, a credential, appear in the attacker's own delivery log. That's server-side request forgery, through D-N-S rebinding.",
 "[+]", "C: Separately, a fraudster POSTs a loan approved event for two thousand four hundred dollars to a till, with a header copied from an old request.",
 "[+]", "C: The till releases a television for a loan that doesn't exist."])

S(dia(K(5, "the fix"), "Check the address you connect to; sign what you send", "ch5-fix", vtag="V5",
      extra=strip(("fixb", "Mechanism", "Egress proxy: resolve, refuse private and metadata ranges, connect to the checked IP; no other route out. HMAC-SHA256 over id.timestamp.body with a per-endpoint secret; reject if |now − t| > 5 min."), cols="one")), [
 "C: The fix, version five: the egress proxy joins the baseline, and the signer changes.",
 "C: One level down on the proxy. Every call leaves through it. It resolves the name itself, refuses private, loopback, link-local and metadata ranges, and connects to the exact address it checked, so a name that changes between check and use gains nothing. Network policy gives dispatchers no other route out. And answers are truncated and scrubbed before they reach a log.",
 "C: On the signature: an H-MAC, SHA two-fifty-six, over the event I-D, the timestamp and the body, with a secret per endpoint from the key service. The till recomputes it, compares in constant time, and rejects anything more than five minutes old. A copied request fails the timestamp; a replayed one inside five minutes is caught by its I-D. " + ps("S2") + " and " + ps("S3") + " hold.",
 "C: What it doesn't cover: a leaked secret, which is rotation. And it's not the tool under it: an A-P-I key in a header proves nothing about the body and can be replayed forever."], cls="dia")

S(dia(K(5, "version 5"), "The egress proxy joins the baseline", "hld-v5", vtag="V5"), [
 "[+]", "C: On the baseline: the dispatcher and the merchant endpoint are carried.",
 "[+]", "C: The egress proxy is new, and it now sits on the only path between them."], cls="dia")

S(dia(K(5, "sequence"), "What the till checks, in order", "seq-ch5-verify"), [
 "C: As a sequence.", "[+]", "C: The dispatcher gets the endpoint's secret from the key service, cached for five minutes.",
 "[+]", "C: It POSTs with the timestamp and the H-MAC over the I-D, the timestamp and the body.",
 "[+]", "C: The till rejects anything older than five minutes.",
 "[+]", "C: It compares in constant time, against the current secret and, during a rotation, the old one.",
 "[+]", "C: And it answers two hundred only after storing the event I-D."], cls="dia")

S(plain(K(5, "defence in depth"), "Never ship goods on a webhook alone", table(["Layer", "What it stops"], [
  ["Egress proxy, no other route", "SSRF, including rebinding"],
  ["Signature with timestamp", "forgery and replay"],
  ["Event ID stored by the till", "replay inside the five minutes"],
  ["Confirm high-value approvals with GET /loans/{id}", "a till that skipped verification"],
  ["Mutual TLS for the partner bank", "anyone but the bank receiving loan-level data"]], "bt sm")), [
 "C: Defence in depth, in layers.", "[+]", "C: The egress proxy, with no other route out, stops request forgery.",
 "[+]", "C: The signature with a timestamp stops forgery and old replays.",
 "[+]", "C: The stored event I-D stops a replay inside the five minutes.",
 "[+]", "C: We tell merchants to confirm a high-value approval by fetching the loan before releasing goods. That protects a till that skipped verification.",
 "[+]", "C: And for the partner bank, mutual T-L-S, so nobody else can receive loan-level data at its U-R-L."])

qs("Interviewer · the second-level push", "“A merchant's secret is on a public code repository. What now?”", [
 "I: A merchant's signing secret has been pushed to a public code repository. What now?", "[pause: 2.0]"])

S(plain(K(5, "the second fix, and the honest limit"), "Rotate with overlap, then revoke", cards(
  ("grn", "Rotate", "A new secret by API; both sign for 24 hours (v1 and v1-old headers), so the till can deploy without dropping events."),
  ("", "Revoke", "After 24 hours, or at once if they choose; every signing is logged with its key ID."),
  ("amb", "Or remove the shared secret", "Asymmetric signatures (Ed25519): we publish a public key, nothing to leak on their side.")) +
  line("Honest limit: asymmetric signing is harder for merchants on old stacks; offer it, keep HMAC as the default.", "r")), [
 "C: Rotate with overlap. The merchant asks for a new secret by A-P-I; for twenty-four hours we sign with both, so their till can deploy without dropping events. Then revoke the old one, or at once if they choose.",
 "C: Or remove the shared secret entirely: asymmetric signatures, where we publish a public key and there's nothing to leak on their side. The honest limit: that's harder for merchants on old stacks, so we offer it and keep H-MAC as the default."])

say_slide("“Every call leaves through a proxy that checks the address it connects to. Every call is signed over its ID, timestamp and body, and too old means rejected. And no one ships goods on a webhook alone.”", [
 "V: If asked, I'd say: every call leaves through a proxy that checks the address it actually connects to. Every call is signed over its I-D, timestamp and body, and too old means rejected. And no merchant should ship goods on a webhook alone.", "[pause: 1.0]",
 "N: The calls are now safe. The next question is about the people who change what is inside them."])

# ───────── Challenge 6 · the payload changes ─────────
subchapter("7.6", "Challenge 6: A producer changes the payload", ["N: Challenge six. A contract problem that is really a team problem: who owns what a merchant parses?"])
qs("Interviewer · challenge 6 of 7", "“The servicing team renames amount to amount_cents and splits status in two. They deploy on Tuesday. What happens on Wednesday?”", [
 "I: The servicing team renames amount to amount cents, and splits status into two fields. They deploy on Tuesday. What happens on Wednesday?", "[pause: 2.0]"])

S(dia(K(6, "the internal event is the contract"), "Every refactor ships to twenty thousand integrations", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Announce it in the changelog; merchants update their parsers.”"), cols="one")), [
 "C: The naive answer: announce it in the changelog, and merchants update their parsers. The matcher, marked red, sends the producer's internal event as it is, so the producer's refactor is everyone's breaking change."], cls="dia")

S(trace(K(6, "the trace"), "A rename on Tuesday, three thousand broken tills on Wednesday", [
  ("Tue 16:00", "servicing deploys: amount → amount_cents; status → state + reason"),
  ("Tue 16:05", "<span class='bad'>3,000 integrations read amount: null; tills show $0 refunds</span>"),
  ("Tue 22:00", "<span class='bad'>accounting imports fail at 1,200 merchants; the partner bank's file breaks</span>"),
  ("Wed 09:00", "<span class='bad'>400 support tickets; servicing says “we own our events”; integrations says “we own merchants”</span>")]), [
 "C: The trace.", "[+]", "C: Tuesday at four, servicing deploys the rename and the split.",
 "[+]", "C: Five minutes later, three thousand integrations read amount as null, and tills show zero-dollar refunds.",
 "[+]", "C: That night, accounting imports fail at twelve hundred merchants, and the partner bank's file breaks.",
 "[+]", "C: By Wednesday morning: four hundred tickets, and two teams who are both right. Servicing owns its events. Integrations owns the merchants. Nobody owns the seam."])

S(dia(K(6, "the fix"), "The public contract is rendered, versioned and owned", "ch6-fix", vtag="V6",
      extra=strip(("fixb", "Mechanism", "Each endpoint pinned to a dated version; the renderer maps internal → public per version; the registry fails a producer's build if any supported version stops rendering; additive in place, breaking = new version, 12 months of support."), cols="one")), [
 "C: The fix, version six: the contract renderer and its schema registry join the baseline. The internal event and the public contract become two different things.",
 "C: One level down. Each endpoint is pinned to a dated version, like two thousand twenty-six, June first. Fan-out's renderer maps the internal event into that version. The registry holds golden examples of every supported public version, and a producer's build fails if any of them stops rendering. That's a consumer-driven contract test, run in the producer's own pipeline.",
 "C: Additive fields go into the current version. A rename or a split is a new dated version, and old versions are supported for twelve months. The rename on Tuesday now changes one mapping in the renderer, and no merchant notices.",
 "C: What it doesn't cover: a change in meaning with the same field name. That's review, not tooling. And it's not the tool under it: freezing one payload forever, which only moves the breakage to the product roadmap."], cls="dia")

S(dia(K(6, "version 6"), "The contract renderer joins the baseline", "hld-v6", vtag="V6"), [
 "[+]", "C: On the baseline: the log, fan-out and the delivery store are carried.",
 "[+]", "C: The contract renderer is new, beside fan-out. Every delivery row now holds the public version its endpoint pinned."], cls="dia")

S(plain(K(6, "the seams"), "Three teams, one side of each contract", table(["Team", "Owns", "Its contract with the others"], [
  ["Producers (origination, servicing)", "internal events and their meaning", "golden examples must still render; additive by default"],
  ["Merchant integrations", "public versions, renderer, docs, SDKs, deprecation", "a version is supported 12 months; usage is measured per endpoint"],
  ["Webhook platform", "relay, fan-out, delivery, egress, health, attempt log", "p99 first attempt, isolation, 72 h; never edits a payload"]], "bt sm") +
  grade("Conway's law on purpose: the seam that broke on Wednesday is now a team's whole job.")), [
 "C: And the seam becomes a team's job.",
 "[+]", "C: The producers own internal events and their meaning. Their contract: the golden examples must still render, and changes are additive by default.",
 "[+]", "C: Merchant integrations owns the public versions, the renderer, the documentation, the S-D-Ks and deprecation. A version is supported for twelve months, and usage is measured per endpoint.",
 "[+]", "C: The webhook platform owns delivery: relay, fan-out, dispatch, egress, health and the attempt log. Its contract is the latency, the isolation and the seventy-two hours, and it never edits a payload.",
 "[+]", "C: That's Conway's law used on purpose. The seam that broke on Wednesday is now one team's whole job."])

qs("Interviewer · the second-level push", "“A security fix needs a breaking change within thirty days. Twelve months is not an option.”", [
 "I: A security fix needs a breaking change within thirty days. Twelve months is not an option.", "[pause: 2.0]"])

S(plain(K(6, "the second fix, and the honest limit"), "Usage telemetry turns deprecation into a list", cards(
  ("grn", "Know who", "Version usage per endpoint: “1,200 endpoints on 2025-01-15” is a list to call, not a guess."),
  ("grn", "Degrade, don't break", "In the old version, redact the unsafe field to null rather than remove it: parsers keep working."),
  ("", "Help them move", "A “send test event” button per version, and a migration guide with a diff.")) +
  line("Honest limit: some merchants will not move in 30 days; the redacted field is the price they pay, not an outage.", "r")), [
 "C: Usage telemetry turns deprecation into a list. We know that twelve hundred endpoints are on an old version, so it's a list to call, not a guess.",
 "C: In the old version, the unsafe field is redacted to null rather than removed, so parsers keep working. And each endpoint gets a send-test-event button per version and a migration guide with a diff. The honest limit: some won't move in thirty days, and the redacted field is the price they pay instead of an outage."])

say_slide("“The internal event is not the contract. Endpoints pin a dated version, a renderer maps to it, producers' builds fail if a supported version stops rendering, and one team owns the public contract.”", [
 "V: If asked, I'd say: the internal event is not the contract. Every endpoint pins a dated version, a renderer maps to it, producers' builds fail if a supported version stops rendering, and one team owns the public contract.", "[pause: 1.0]",
 "N: Last challenge: when a merchant says something went wrong, how would you know?"])

# ───────── Challenge 7 · how would you know ─────────
subchapter("7.7", "Challenge 7: “You never sent it”", ["N: Challenge seven, observability. The dashboards are green and a merchant is angry."])
qs("Interviewer · challenge 7 of 7", "“A merchant says you never sent loan.funded for ln_7781. Your dashboards are green. Who is right?”", [
 "I: A merchant says we never sent loan funded for loan seventy-seven eighty-one. Our dashboards are green. Who is right?", "[pause: 2.0]"])

S(dia(K(7, "silence"), "Green, because the failure is theirs, and nobody told them", "ch7-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Platform success is 99.9 %; it's on their side.”"), cols="one")), [
 "C: The naive answer: platform success is ninety-nine point nine percent, so it's on their side. The attempt log, marked red, has the answer, and nobody is looking at it."], cls="dia")

S(trace(K(7, "the trace"), "Three days of 401s that only we could see", [
  ("Fri 17:00", "the merchant rotates their own gateway credentials"),
  ("Fri 17:02", "every delivery to them answers 401"),
  ("Mon 09:00", "<span class='bad'>8,000 deliveries dead or retrying; platform success 97 %, as every day (600 endpoints failing)</span>"),
  ("Mon 10:00", "<span class='bad'>support has no per-delivery view; “it's on your side” starts a week of email</span>")]), [
 "C: The trace.", "[+]", "C: On Friday at five, the merchant rotates their own gateway credentials.",
 "[+]", "C: From then on, every delivery to them answers four-oh-one.",
 "[+]", "C: By Monday, eight thousand deliveries are dead or retrying. Platform success reads ninety-seven percent, exactly as on every other day, because six hundred endpoints are always failing.",
 "[+]", "C: Support has no per-delivery view, and it's on your side starts a week of email."])

S(dia(K(7, "the fix"), "Show the merchant every attempt; page us only on what we own", "ch7-fix",
      extra=strip(("fixb", "Mechanism", "Per-delivery attempts in the merchant's dashboard; endpoint health emails after 1 h failing; our SLIs: first-attempt p99 per tier, success to healthy endpoints, oldest pending age, relay and fan-out lag."), cols="one")), [
 "C: The fix splits observability in two. For the merchant: every attempt for every delivery in their dashboard, with status, latency and the first bytes of the answer, and an email from endpoint health after an hour of failures. The merchant would have seen four-oh-one on Friday evening.",
 "C: For us, only what we own. First-attempt p ninety-nine per tier. Success to healthy endpoints, those that succeeded ninety-nine percent of the time over the last day, which is what moves when we break. The age of the oldest pending delivery per tier. And relay and fan-out lag. None of these moves when a merchant breaks their own server, and all of them move when we do."], cls="dia")

S(plain(K(7, "symptom pairs"), "Two metrics, one conclusion", table(["Metric A", "Metric B", "Conclusion"], [
  ["first-attempt p99 up, every tier", "fan-out lag up", "us: fan-out or the renderer"],
  ["first-attempt p99 up, every tier", "relay lag up", "us: a producer's relay"],
  ["failures up at one endpoint", "everyone else flat", "them: tell them, page nobody"],
  ["success to healthy endpoints down", "egress denials up", "us: the proxy or DNS"],
  ["oldest pending age up, one tier", "that tier's pool saturated", "a cap or a pool size"]], "bt sm") +
  grade("A merchant's outage must never page us, and ours must page us before any merchant notices.")), [
 "C: Then read them in pairs.", "[+]", "C: First-attempt latency up in every tier, with fan-out lag up: it's us, fan-out or the renderer.",
 "[+]", "C: The same latency, with relay lag up: a producer's relay.",
 "[+]", "C: Failures up at one endpoint, everyone else flat: it's them. Tell them, page nobody.",
 "[+]", "C: Success to healthy endpoints down, with egress denials up: the proxy or D-N-S.",
 "[+]", "C: And the oldest pending age up in one tier, with its pool saturated: a cap or a pool size.",
 "[+]", "C: A merchant's outage must never page us, and ours must page us before any merchant notices."])

qs("Interviewer · the second-level push", "“The merchant now says your signatures don't verify.”", [
 "I: The merchant now says our signatures don't verify.", "[pause: 2.0]"])

S(plain(K(7, "the second fix"), "Make the signature debuggable", cards(
  ("grn", "Keep what we sent", "The attempt log stores the timestamp, the key ID and the signature header of every attempt."),
  ("grn", "A test tool", "“Send test event” plus a page that recomputes the signature from a pasted body."),
  ("", "The usual causes", "Re-serialised JSON, a clock more than 5 minutes off, the old secret after a rotation.")) +
  line("Honest limit: we never log the secret; the tool runs in their browser or with their SDK.", "r")), [
 "C: Make the signature debuggable. The attempt log keeps the timestamp, the key I-D and the signature header for every attempt. The dashboard has a send-test-event button and a page that recomputes the signature from a pasted body.",
 "C: The usual causes are three: their framework re-serialised the jason before verifying, their clock is more than five minutes off, or they still use the old secret after a rotation. The honest limit: we never log the secret, so the check runs in their browser or their S-D-K."])

say_slide("“I show the merchant every attempt and tell them when their endpoint fails. I page us only on what we own: first-attempt latency per tier, success to healthy endpoints, the oldest pending age, and lag.”", [
 "V: If asked, I'd say: I show the merchant every attempt and tell them when their endpoint fails. I page us only on what we own: first-attempt latency per tier, success to healthy endpoints, the oldest pending delivery, and lag.", "[pause: 1.0]"])

# ───────────────────────── 8 · build cost ─────────────────────────
chapter(8, "Build cost", 6, "The manager layer: people, quarters, seams, buy against build", [
 "N: This chapter is marked auxiliary. It is the engineering-manager layer, optional in a Staff round, central in a manager round.",
 "C: The platform is six versions, and the order matters more than the size."], aux=True)

S(plain("Build cost · releases", "Six versions, riskiest first", table(["", "Scope", "People · time (illustrative)"], [
  ["V2", "outbox library and relay; the log is already there", "2 engineers, 1 quarter, with the producers"],
  ["V3", "fan-out, delivery store, dispatcher with caps, attempt log, API", "a team of 5, 2 quarters"],
  ["V4", "endpoint health: breaker, ramp, disable, replay", "the same team, 1 quarter"],
  ["V5", "egress proxy, signing, rotation", "1 engineer + security, 1 quarter"],
  ["V6", "registry, renderer, versions, SDKs", "merchant integrations, 2 engineers, ongoing"]], "bt sm")), [
 "C: The releases.", "[+]", "C: Version two, the outbox library and relay, two engineers for a quarter, built with the producing teams. The log is already there.",
 "[+]", "C: Version three, the core: fan-out, the delivery store, the dispatcher with its caps, the attempt log and the A-P-I. A team of five, two quarters. This is the riskiest work, so it goes first, with a load test of one slow endpoint before anything ships.",
 "[+]", "C: Version four, endpoint health, the same team for a quarter.",
 "[+]", "C: Version five, the egress proxy and signing, one engineer with the security team.",
 "[+]", "C: And version six, the contract, is not a project but a team: merchant integrations, two engineers, for as long as there are merchants."], cls="aux")

S(plain("Build cost · contracts between teams", "Every contract has one owner and a rule for change", table(["Contract", "Owner → consumers", "Rule"], [
  ["Outbox row and internal event", "producers → platform", "additive; event ID and loan sequence always present"],
  ["Public versions", "integrations → merchants", "dated; 12 months; usage measured per endpoint"],
  ["Delivery SLOs", "platform → integrations, merchants", "p99 first attempt, isolation, 72 h"],
  ["Golden examples", "integrations → producers' builds", "a producer's build fails if a version stops rendering"]], "bt sm") +
  grade("Draw the contracts first, then give each team one side. A change to a contract needs both sides.")), [
 "C: The contracts between the teams.", "[+]", "C: The outbox row and internal event: producers to the platform. Additive, and the event I-D and loan sequence are always present.",
 "[+]", "C: The public versions: integrations to merchants. Dated, twelve months of support, usage measured per endpoint.",
 "[+]", "C: The delivery objectives: the platform to integrations and merchants. First-attempt latency, isolation, seventy-two hours.",
 "[+]", "C: And the golden examples: integrations to the producers' builds. A producer's build fails if a supported version stops rendering.",
 "[+]", "C: Draw the contracts first, give each team one side, and require both sides for a change."], cls="aux")

S(plain("Build cost · buy, run, risk", "What I would buy, how it is run, what could sink it", cards(
  ("", "Buy against build", "At 180 M a month a managed delivery engine is ≈ $18k a month: a serious option if the bank allows it. Build past ≈ 800 M, or when data must stay."),
  ("grn", "On-call", "The platform pages on its own lag and on success to healthy endpoints; merchants' failures go to them by email, never to our pager."),
  ("red", "Top risks", "A producer bypassing the outbox. A cap tuned too high. The proxy as a single point. A public version nobody owns."), cols=3)), [
 "C: Buy against build, as in the alternate path: at a hundred and eighty million a month, a managed delivery engine costs about eighteen thousand dollars a month, a serious option if the partner bank allows it. Build past about eight hundred million, or when the data must stay with us.",
 "C: On-call: the platform pages on its own lag and on success to healthy endpoints. Merchants' failures go to them, by email, and never to our pager.",
 "C: And the top risks: a producer that bypasses the outbox, a cap tuned too high, the proxy as a single point of failure, which runs in every zone, and a public version that nobody owns."], cls="aux")

# ───────────────────────── 9 · recap ─────────────────────────
chapter(9, "Recap", 7, "One picture, seven paths, the mistakes, the thesis", [
 "C: The recap: the final design once more, one sentence per path, the common mistakes, and the thesis."])

S(dia("Recap · the final design", "Version six, along the path of one event", "base-final"), [
 "C: The final design, along the path of one event.", "[+]", "C: One: the producer commits the change and its outbox row.",
 "[+]", "C: Two: the relay publishes it to the log.", "[+]", "C: Three: fan-out consumes it,", "[+]", "C: four: renders each endpoint's public version,",
 "[+]", "C: five: and writes one delivery row per endpoint.", "[+]", "C: Six: the dispatcher claims it under the endpoint's cap.",
 "[+]", "C: Seven: signs it and sends it through the egress proxy,", "[+]", "C: eight: to the merchant's checked address. Below them, the attempt log, the A-P-I and endpoint health close the loop."], cls="dia")

S(plain("Recap · seven paths", "One sentence each", table(["Path", "In one sentence"], [
  ["Emit", "the outbox row is in the commit; the relay publishes at least once"],
  ["Fan out", "one event becomes one row per endpoint, rendered to its version"],
  ["Deliver", "claimed under a cap, signed, through a proxy that checks the address"],
  ["Recover", "full jitter, a breaker, a ramp; dead after 72 h; replay at their rate"],
  ["Trust", "ID, sequence, timestamp, signature; never ship goods on a webhook alone"],
  ["Evolve", "dated versions, a renderer, producers' builds that fail first"],
  ["Observe", "the merchant sees every attempt; we page only on what we own"]], "bt sm")), [
 "C: Seven paths, one sentence each.", "[+]", "C: Emit: the outbox row is in the commit, and the relay publishes at least once.",
 "[+]", "C: Fan out: one event becomes one row per endpoint, rendered to its version.",
 "[+]", "C: Deliver: claimed under a cap, signed, through a proxy that checks the address.",
 "[+]", "C: Recover: full jitter, a breaker and a ramp; dead after seventy-two hours; replay at their rate.",
 "[+]", "C: Trust: I-D, sequence, timestamp and signature, and never ship goods on a webhook alone.",
 "[+]", "C: Evolve: dated versions, a renderer, and producers' builds that fail first.",
 "[+]", "C: Observe: the merchant sees every attempt, and we page only on what we own."])

S(plain("Recap · common mistakes", "What costs points in this round", cards(
  ("red", "Design", "A POST inside the business request. One shared queue and pool. Retries in memory. Kafka retry topics as the per-endpoint queue."),
  ("amb", "Judgement", "Promising exactly-once or strict order. Trusting a URL string. An API key instead of a signature. The internal event as the public contract. Paging on merchants' errors."))), [
 "N: The mistakes that cost points. In the design: a POST inside the business request, one shared queue and pool, retries in memory, and retry topics used as a queue per endpoint.",
 "N: In judgement: promising exactly-once or strict order, trusting a U-R-L string, an A-P-I key instead of a signature, the internal event as the public contract, and paging on merchants' errors."])

key("The close", "We promise <em>at-least-once</em> and give every endpoint its <em>own failure budget</em>. Exactly-once is the <em>consumer's</em> job, and the <em>contract</em> that makes it possible is the product.", [
 "V: We promise at-least-once delivery, and give every endpoint its own failure budget. Exactly-once is the consumer's job, and the contract that makes it possible is the product.", "[pause: 1.2]"])

followups([
 ("What if a merchant's endpoint is down for a week?", "Challenge 3 and the 72-hour rule"),
 ("How do you stop a hostile endpoint attacking us?", "Challenge 5; mechanism six"),
 ("How do you change a payload shape without breaking merchants?", "Challenge 6; mechanism five"),
 ("When would you buy instead of build?", "Option F; the alternate path"),
 ("How do you prove to a merchant that you sent it?", "Challenge 7; the attempt log"),
 ("What changes at ten times the volume?", "Option D, its write cost; the shard count")], [
 "N: Questions you should be ready for next. Each points back to where this video answers it.", "[+]", "C: An endpoint down for a week: challenge three, and the seventy-two-hour rule.", "[+]",
 "C: A hostile endpoint: challenge five, and the egress proxy.", "[+]", "C: A payload change: challenge six, and the consumer contract.", "[+]",
 "C: Buy against build: option F, and the alternate path.", "[+]", "C: Proving we sent it: challenge seven, and the attempt log.", "[+]", "C: And ten times the volume: option D's write cost, and the shard count."])
