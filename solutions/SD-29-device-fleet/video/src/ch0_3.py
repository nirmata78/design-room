from dsl import *
P = "[+]"

chapter(0, "Cold open", -1, "Control a million devices you cannot touch", [
 "C: Pushing configuration to devices sounds like a message queue. It's asked at Google, Amazon and Microsoft, and at every company with hardware in the field, because the devices are offline when you need them, untrusted, impossible to reach physically, and alive for seven years. A bad push is a fleet-wide outage with a schedule."])

qs("Interviewer · the prompt", "“Design the control plane for a million devices in the field: know their state, push configuration and software to them, and do it without bricking the fleet.”", [
 "I: Design the control plane for a million devices in the field. Know their state, push configuration and software to them, and do it without bricking the fleet.", "[pause: 1.5]"])

S(dia("Why it is harder than it looks", "Reach every device, or never break one", "tension", chip=chips("fast is dangerous", "frozen is dangerous", "waves that stop themselves")), [
 "C: The hook. Move fast: push to everyone in a day, and a bad image bricks a million devices. At a hundred and fifty dollars a truck roll, that's a hundred and fifty million dollars.",
 "C: Move never, and seven years of devices run unpatched software. The design lives in the third box: move in waves that start with every kind of hardware, stop themselves on a bad signal, and devices that roll themselves back without anyone reaching them."])

S(plain("Before the design", "What this question grades", table(["Axis", "Weak signal", "Strong signal"], [
  ["<b>Requirements</b>", "“Push updates to devices”", "Asks how often devices are offline, and what a bricked device costs"],
  ["<b>Correctness</b>", "Commands sent to online devices", "Desired against reported state, reconciled; latest wins"],
  ["<b>Safety</b>", "Percentage rollouts, watched by a person", "Cohorts, automatic halt, A/B partitions and a watchdog"],
  ["<b>Depth</b>", "“Use MQTT”", "Per-device identity, signed images, jittered backoff, admission control"],
  ["<b>Operations</b>", "Connected-device count", "Convergence time, version census, wave-against-control health"]], "bt xs sig") +
  grade("Design for the device you cannot reach, not the one that is online.")), [
 "N: Five axes.", P, "N: Requirements: the strong answer asks how often devices are offline and what a bricked device costs.", P,
 "N: Correctness: not commands to online devices, but desired against reported state, reconciled.", P,
 "N: Safety: not a percentage watched by a person, but cohorts, an automatic halt, and devices that roll back on their own.", P,
 "N: Depth: identity per device, signed images, jittered backoff, admission control.", P,
 "N: Operations: convergence time and a version census, not the connected-device count.", P,
 "C: And the rule for the round: design for the device you can't reach, not the one that's online."])

key("The thesis", "Never send a device a command; publish a <em>desired state</em> it converges to whenever it can. Release in <em>waves that halt themselves</em>, and give every device a <em>last known good</em> it returns to on its own.", [
 "V: Never send a device a command. Publish a desired state it converges to whenever it can. Release in waves that halt themselves, and give every device a last known good it returns to on its own.", "[pause: 1.0]"])

S(plain("The order I will follow", "Scope, numbers, theory, a simple design, then I break it",
  '<div class="ribbon" style="margin-top:6pt">' + "".join(f"<span>{x}</span>" for x in STAGES) + '</div>' +
  cards(("", "First", "Requirements, the dangerous numbers, and the theory: reconciliation, identity, waves, partitions, backoff."),
        ("grn", "Then", "The interfaces and the data, three versions on one picture, every path, three containers one level down."),
        ("red", "Most of the time", "Six challenges, from a device that cannot boot to a fleet that never converges."), cols=3)), [
 "C: The order I'll follow.", P,
 "C: First, requirements, the dangerous numbers, and the theory: reconciliation, identity, waves, A-B partitions and backoff.", P,
 "C: Then the interfaces and the data, three versions on one picture, every path, and three containers opened up.", P,
 "C: Then six challenges, from a device that can't boot to a fleet that never converges."])

chapter(1, "Requirements and scope", 0, "The scale first, then five questions", ["C: The scale first, then five questions."])

S(plain("Requirements · the scale line", "Three numbers every estimate starts from", '<div class="tiles" style="--n:3">'
  '<div class="tile blue"><b>1 M</b><span>devices; a release a month, 30 configs</span></div>'
  '<div class="tile"><b>7 years</b><span>in the field; 8.6 B health reports a month</span></div>'
  '<div class="tile red"><b>200,000</b><span>reconnect in one minute after an ISP outage</span></div></div>' +
  line("Every number later starts from one of these three.", "a")), [
 "C: The scale.", P, "C: A million devices, a firmware release a month and about thirty configuration changes.", P,
 "C: Each lives seven years in the field, and sends a health report every five minutes: about eight point six billion a month.", P,
 "C: And the peak: a regional internet provider recovers, and two hundred thousand devices reconnect in the same minute.", P,
 "C: Every number later starts from these."])

def clar(n, q, a, ask, ans, so):
    S(f'<div class="who">Clarifying question {n} of 5</div><div class="qq">{q}</div><div class="ans">{a}</div>',
      ["C: " + ask, P, "I: " + ans, "C: " + so], cls="qs")

clar(1, "How often are devices offline?", "Intermittently every day; some for weeks.",
     "How often are devices offline?", "Intermittently every day. Some for weeks.",
     "Then nothing can depend on a device being online when we act. A device must catch up on its own.")
clar(2, "What does a bricked device cost?", "A truck roll: about $150 and a day for the customer.",
     "What does a device that won't boot cost us?", "A truck roll: about a hundred and fifty dollars, and a day for the customer.",
     "That sets the blast-radius budget for a release. A hundred devices is fifteen thousand dollars; a percent of the fleet is a million and a half.")
clar(3, "How different are the devices?", "Five hardware revisions, three cellular carriers, every region.",
     "How different are the devices from each other?", "Five hardware revisions, three cellular carriers, every region.",
     "So a percentage isn't a sample. The first wave must contain every combination that can fail differently.")
clar(4, "Can we trust a device?", "No. Assume any device can be stolen and probed.",
     "Can we trust what a device sends?", "No. Assume any device can be stolen and taken apart.",
     "Identity per device, from manufacture, and a device can touch only its own state.")
clar(5, "What is in scope?", "Config, firmware, state and health. Not the device's application data.",
     "What's in scope?", "Configuration, firmware, state and health. Not the application data the devices produce.",
     "That's the control plane. The data plane is someone else's pipeline, like question ninety-seven's.")

S(plain("Requirements · functional", "Four things the system must do", cards(
  ("", "FR1 · Know", "Every device’s reported state and health, current when it last connected."),
  ("grn", "FR2 · Configure", "Set desired configuration for a device or cohort; devices converge when they can."),
  ("amb", "FR3 · Release", "Roll out signed firmware in waves, each soaked and compared before the next."),
  ("red", "FR4 · Stop", "Halt and revert a bad change automatically, including on devices that cannot boot it."))), [
 "C: Four functional requirements.", P, "C: One, know every device's reported state and health.", P,
 "C: Two, configure a device or a cohort, and devices converge when they can.", P,
 "C: Three, release signed firmware in waves, each soaked and compared before the next.", P,
 "C: Four, stop: halt and revert a bad change automatically, including on devices that can't even boot it."])

S(plain("Requirements · non-functional", "The numbers, and what each is for", '<p class="chips">all initial targets</p><div class="tiles" style="--n:4">'
  '<div class="tile red"><b>≤ 100</b><span>devices harmed by any one release</span></div>'
  '<div class="tile blue"><b>95 % in 24 h</b><span>of online devices converge to a config</span></div>'
  '<div class="tile"><b>2 weeks</b><span>a full firmware release</span></div>'
  '<div class="tile blue"><b>99.9 %</b><span>control plane; devices run without it</span></div></div>' +
  line("If the control plane is down, devices keep running their last good state.", "a")), [
 "C: The numbers.", P, "C: At most a hundred devices harmed by any one release: fifteen thousand dollars.", P,
 "C: Ninety-five percent of online devices on a new config within a day.", P, "C: A full firmware release in about two weeks.", P,
 "C: Three nines for the control plane, because devices don't need it to run.", P,
 "C: If it's down, devices keep running their last good state. That's static stability."])

S(plain("Requirements · scope", "In, and out on purpose", cards(
  ("grn", "In scope", "Identity, sessions, desired and reported state, configs, firmware waves, halts, device-side recovery, fleet health."),
  ("red", "Out, on purpose", "The devices' application data, manufacturing, the PKI itself, billing, customer dashboards.")) +
  line("The data plane is a different system with a different budget: SD-97 is its question.", "")), [
 P, "C: In scope: identity and sessions, desired and reported state, configurations, firmware waves and halts, the recovery on the device, and fleet health.", P,
 "C: Out, on purpose: the application data the devices produce, manufacturing, running the P-K-I itself, billing, customer dashboards.", P,
 "C: The data plane is a different system with a different budget. Question ninety-seven is its question."])

S(dia("Architecture · C4 level 1 · context", "The system in its context", "c4-context",
      cap="Figure 1.1 — C4 system context: devices, operators, the factory PKI and the image CDN"), [
 "C: The context.", P, "C: A million devices in the field, often offline, and a truck roll away.", P, "C: The fleet platform, one box.", P,
 "C: Operators change configuration and release firmware.", P, "C: The factory P-K-I gives every device a key at manufacture.", P,
 "C: And a C-D-N serves signed firmware images."], cls="dia")

key("The core", "The core is three things: a <em>shadow</em> of desired and reported state, a <em>rollout that halts itself</em>, and a <em>device that recovers itself</em>.", [
 "V: The core is three things. A shadow of desired and reported state. A rollout that halts itself. And a device that recovers itself.", "[pause: 0.8]"])

chapter(2, "Estimates", 1, "Each number from the scale line, with what it decides", ["C: Numbers next, each from the scale line. Illustrative."])

S(plain("Estimates · steady state", "A million quiet devices are a small load", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Health reports", "1 M every 5 min", "1 M ÷ 300 s ≈ <b>3,300/s</b> × 1 KB ≈ 3.3 MB/s", "Kafka and a TSDB, small"],
  ["Connections", "1 M devices", "1 M ÷ 100,000 per node = <b>10 nodes</b>, ×2 headroom", "An MQTT cluster of 20"],
  ["Shadow", "1 M devices", "1 M × 4 KB ≈ <b>4 GB</b>", "One PostgreSQL, with a standby"]])), [
 "C: Steady state.", P, "C: A million devices every five minutes is about thirty-three hundred health reports a second, three megabytes a second. Small.", P,
 "C: A million persistent connections at a hundred thousand per node is ten nodes; I'd run twenty.", P,
 "C: And the shadow: four kilobytes per device is four gigabytes. One PostgreSQL with a standby."])

S(plain("Estimates · the dangerous numbers", "What a storm and a bad release cost", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Reconnect storm", "200,000 in a minute", "≈ <b>3,300 connects/s</b>; without jitter, in 5 s: 40,000/s", "Jitter and admission control"],
  ["A release", "50 MB × 1 M", "<b>50 TB</b>; deltas ≈ 8 MB → 8 TB", "A CDN, never the brokers"],
  ["Bricking 1 %", "$150 a visit", "10,000 × $150 = <b>$1.5 M</b>", "Waves; a budget of 100 devices"],
  ["Version tail", "7 years, monthly", "up to <b>84</b> versions ever shipped", "Every protocol version stays supported"]])), [
 "C: The dangerous numbers.", P,
 "C: Two hundred thousand reconnects in a minute is thirty-three hundred a second. If they all retry at once, in five seconds, forty thousand a second, each a T-L-S handshake. That decides jitter and admission control.", P,
 "C: A release: fifty megabytes to a million devices is fifty terabytes; with delta images, eight. A C-D-N, never the brokers.", P,
 "C: Bricking one percent costs a million and a half dollars. So waves, with a blast-radius budget of a hundred devices.", P,
 "C: And seven years of monthly releases is up to eighty-four versions in the field. The server must keep speaking every protocol it ever shipped."])

S(plain("Estimates · identity", "A million certificates expire too", table(["Number", "From", "Arithmetic", "Decides"], [
  ["Certificates", "1 M devices", "2-year validity: 1 M ÷ 730 days ≈ <b>1,400 renewals a day</b>", "Automatic renewal over the session"],
  ["Offline at expiry", "weeks offline", "a device back after its certificate expired", "A grace window, then a re-enrolment path"],
  ["A stolen device", "any one", "its key reaches only its own topics", "Revoke one certificate; nothing else changes"]])), [
 "C: Identity has numbers too.", P,
 "C: A million certificates valid for two years is about fourteen hundred renewals a day. They must renew themselves, over the session, without a person.", P,
 "C: A device offline when its certificate expired comes back with an expired key. A grace window lets it renew; past that, a re-enrolment path signed with the factory key.", P,
 "C: And a stolen device's key reaches only its own topics. Revoking one certificate changes nothing else."])

S(dia("Estimates · the release budget", "Two weeks, from the first device to the last", "budget", chip=chips("initial target")), [
 "C: The release budget. Two days for waves zero and one, two for wave two, a day waiting for a person's approval, two for wave three, three for the rest: about ten days of fourteen.",
 "C: The spare is for a halted wave, which is the normal case for one release in five, not an emergency."], cls="dia")

chapter(3, "Theory", 2, "Reconciliation, identity, waves, partitions, backoff", [
 "C: The theory: what makes this hard, beyond product names. Five mechanisms, the options, what will go wrong."])

S(plain("Theory · what it is", "A control loop over devices you cannot reach", cards(
  ("", "It is", "Keeping a million unreachable, untrusted devices converging to a desired state, safely."),
  ("amb", "Not a message bus", "A bus delivers to whoever is listening; most devices are not."),
  ("amb", "Not telemetry", "Telemetry is the data plane; here health is only the signal for decisions."),
  ("amb", "Not app deployment", "A server can be replaced; a device must survive its own bad update."), cols=2)), [
 "C: What it is, and what it isn't.", P, "V: Keeping a million unreachable, untrusted devices converging to a desired state, safely.", P,
 "C: Not a message bus: a bus delivers to whoever is listening, and most devices aren't.", P,
 "C: Not telemetry: health is only the signal for decisions here.", P,
 "C: And not app deployment: a server can be replaced; a device must survive its own bad update."])

S(plain("Theory · properties", "Safety and liveness, stated separately", cards(
  ("red", "S1 · never bricked", "No update leaves a device unable to boot a working image."),
  ("red", "S2 · only signed, only its own", "A device runs only signed images and accepts only its own desired state."),
  ("red", "S3 · bounded harm", "A bad release reaches at most its first wave."),
  ("grn", "L1 · converge", "Every device that comes online converges to the latest desired state."),
  ("grn", "L2 · finish", "A good release reaches the fleet in about two weeks."), cols=3)), [
 "C: Safety.", P, "V: S-one: no update leaves a device unable to boot a working image.", P,
 "V: S-two: a device runs only signed images, and accepts only its own desired state.", P,
 "V: S-three: a bad release reaches at most its first wave.", P,
 "C: Liveness: L-one, every device that comes online converges to the latest desired state.", P,
 "C: L-two, a good release finishes in about two weeks. Being too careful is also a failure."])

def mech(n, name, prot, how, rules, cost, say):
    S(plain(f"Theory · mechanism M{n}", name, cards(("", "Protects", prot), ("grn", "How it works", how), ("red", "Rules out", rules), ("amb", "Costs", cost), cols=2)), say)

mech(1, "Desired and reported state, reconciled", "L1.", "Store a versioned desired document and the reported one per device; the device pulls and applies the latest; a loop nudges the drift.",
     "Commands lost to offline devices; replaying stale changes in order.", "A device must be able to compute “apply this whole state”.", [
 "C: Mechanism one: desired and reported state, reconciled.", P, "C: It protects L-one.", P,
 "C: Each device has a versioned desired document and a reported one. The device pulls the latest desired state whenever it connects and applies all of it. A reconciler nudges devices whose reported version lags.", P,
 "C: It rules out commands lost to offline devices, and replaying a queue of stale changes.", P,
 "C: It costs this: the device must apply a whole state, not a delta."])

mech(2, "Identity per device, and signed images", "S2.", "A key pair from the factory, mutual TLS on every connection, topics scoped to the device; images signed offline and verified on the device.",
     "One stolen device reading or changing others; a compromised CDN installing code.", "A PKI and a signing ceremony to run.", [
 "C: Mechanism two: identity per device, and signed images.", P, "C: It protects S-two.", P,
 "C: Each device gets a key pair at the factory, presents its certificate on every connection, and may touch only topics with its own I-D. Firmware is signed offline, and the device verifies the signature before writing it.", P,
 "C: It rules out one stolen device reaching the others, and a compromised C-D-N installing code.", P,
 "C: It costs a P-K-I and a signing ceremony."])

mech(3, "Waves by cohort, with an automatic halt", "S3, L2.", "Release to small waves that include every hardware rev, region and carrier; compare each wave with a control; halt on a significant difference.",
     "A rare hardware revision bricking at 10 %; a person noticing too late.", "Days of soak; a statistic to trust.", [
 "C: Mechanism three: waves by cohort, with an automatic halt.", P, "C: It protects S-three, and L-two.", P,
 "C: Release to a small wave that contains every hardware revision, region and carrier. Soak it, compare its health with a control group, and halt automatically when the difference is real.", P,
 "C: It rules out a rare revision bricking at ten percent, and a person noticing too late.", P, "C: It costs days of soak, and a statistic people must trust."])

mech(4, "A/B partitions with a watchdog", "S1.", "Write the new image to the inactive slot; boot it with a try counter; the agent must confirm health before a hardware timer fires, or the bootloader reverts.",
     "A device stuck in a crash loop no server can reach.", "Twice the flash for images; a slower first boot.", [
 "C: Mechanism four, the crux of S-one: A-B partitions with a watchdog.", P, "C: It protects S-one.", P,
 "C: The new image goes into the inactive slot. The bootloader boots it with a try counter. The agent must confirm it's healthy, which includes reaching the server, before a hardware watchdog fires. If it doesn't, the counter runs out and the bootloader returns to the last good slot.", P,
 "C: It rules out a crash loop that no server can reach.", P, "C: It costs twice the flash, and a slower first boot."])

mech(5, "Jittered backoff and admission control", "L1, availability.", "Retry after a random delay up to a growing cap; brokers admit new connections through a token bucket and answer “later” with a hint.",
     "200,000 devices retrying in lockstep and keeping the cluster down.", "Slower recovery for some devices.", [
 "C: Mechanism five: jittered backoff and admission control.", P, "C: It protects L-one and the control plane itself.", P,
 "C: A device retries after a random delay up to a growing cap. Brokers admit new connections through a token bucket per node and answer later, with a hint, when it's empty.", P,
 "C: It rules out two hundred thousand devices retrying in step and keeping the cluster down.", P, "C: It costs a slower recovery for some devices."])

S(dia("Theory · mechanism M4 at work", "A new image that never confirms", "seq-th-ab"), [
 "C: Mechanism four at protocol level.", P, "C: The bootloader marks slot B to try, three tries left.", P, "C: It boots version four point three.", P,
 "C: The agent must confirm it's healthy within a hundred and twenty seconds.", P,
 "C: It doesn't. The watchdog resets the device: two tries, one, none.", P, "C: Tries exhausted: boot version four point two from slot A.", P,
 "C: And report that it rolled back. No server was involved."], cls="dia")

S(plain("Theory · edge against level", "Why a device reads state, not events", table(["", "Edge-triggered (events)", "Level-triggered (state)"], [
  ["What is sent", "“change display to eco”", "“the desired state is v18”"],
  ["A device offline for a week", "misses events, or replays a queue", "reads v18 when it returns"],
  ["A lost message", "a lost change", "the next comparison catches it"],
  ["A duplicate", "applied twice, unless idempotent", "v18 twice is a no-op"]], "bt sm")), [
 "C: One idea under mechanism one is worth its own slide: edge against level.", P,
 "C: An edge-triggered system sends events: change the display to eco. A level-triggered one publishes state: the desired state is version eighteen.", P,
 "C: A device offline for a week misses events, or replays a queue. With state, it reads eighteen when it returns.", P,
 "C: A lost event is a lost change. A lost state message is caught by the next comparison.", P,
 "C: And a duplicate event is applied twice unless you're careful; version eighteen twice is a no-op. That's why every loop in this design compares, then converges."])

S(plain("Theory · the options", "Five ways to build it, one picked", table(["Approach", "Offline-safe", "Brick-safe", "Fails when"], [
  ["A · the server pushes commands", "no", "no", "a device offline at the moment misses it forever"],
  ["B · devices poll a config URL", "yes", "no", "no versions, no reported state, no rollback"],
  ["C · shadow + reconcile, pushed to everyone", "yes", "no", "one bad image reaches the fleet in a day"],
  ["D · shadow + waves by percentage, a person watching", "yes", "partly", "a rare hardware rev isn’t in 1 %; humans are slow"],
  ("pick", ["<b>E · shadow, waves by cohort with auto-halt, A/B + watchdog</b>", "yes", "yes", "weeks per release; flash for two images"])], "bt xs mx") +
  line("Converge when you can, release in steps that stop themselves, recover without help.", "a")), [
 "C: Five ways.", P, "C: A: the server pushes commands. A device offline at that moment misses them.", P,
 "C: B: devices poll a configuration U-R-L. No versions, no reported state, no rollback.", P,
 "C: C: a shadow and reconciliation, pushed to everyone at once. One bad image reaches the fleet in a day.", P,
 "C: D: waves by percentage with a person watching. A rare hardware revision isn't in one percent, and people are slow.", P,
 "C: E, which I pick: a shadow, waves by cohort with an automatic halt, and A-B partitions with a watchdog.", P,
 "V: Converge when you can, release in steps that stop themselves, and recover without help.", "[pause: 0.8]"])

S(plain("Theory · the failure catalogue", "What will go wrong, in the order I'll take it", table(["#", "Failure", "At risk"], [
  ["1", "A config that crashes the device on boot", "S1"],
  ["2", "A release that bricks one rare hardware revision", "S3"],
  ["3", "A device offline for six weeks and four changes", "L1"],
  ["4", "200,000 devices reconnect in one minute", "L1, availability"],
  ["5", "Buffered telemetry arrives twice, from a device ID label", "decisions"],
  ["6", "Every device “connected”, the fleet not converging", "all"]], "bt sm")), [
 "C: The failure catalogue.", P, "C: One: a config that crashes the device on boot.", P, "C: Two: a release that bricks one rare hardware revision.", P,
 "C: Three: a device offline for six weeks and four changes.", P, "C: Four: two hundred thousand reconnects in a minute.", P,
 "C: Five: buffered telemetry arriving twice.", P, "C: Six: every device connected, and the fleet not converging."])
