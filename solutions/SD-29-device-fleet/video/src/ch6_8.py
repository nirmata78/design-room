from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

chapter(6, "Bridge", 5, "It works. Where does it break first?", ["V: It works. The question now is where it breaks first.", "[pause: 1.0]"])
S(dia("Challenge map", "Six challenges, five places on the same picture", "map", chip=chips("each fix creates the next question")), [
 P, "C: Version three, with the places it breaks.", P, "C: The device agent: a config that crashes it on boot. Challenge one.", P,
 "C: The rollout controller: a release that bricks one rare revision. Challenge two.", P,
 "C: The shadow store: a device back after six weeks and four changes. Challenge three.", P,
 "C: The gateway: two hundred thousand reconnects in a minute. Challenge four.", P,
 "C: And telemetry: duplicates and a cardinality trap. Challenge five. Then, how would we know?"], cls="dia")

chapter(7, "Challenges", 5, "Six ways to break it, and what survives", ["C: Six challenges, each the same way: the question, the naive answer, a case with numbers, where it breaks inside the container, the fix one level down, then the push on the fix itself, and what I would say in the room."])

# ── 1
subchapter("7.1", "Challenge 1: A config that crashes the device", ["N: Challenge one is the crux: the device you can no longer reach."])
qs("Interviewer · challenge 1 of 6", "“You push a config that crashes the device on boot. It's now offline. What saves you?”", [
 "I: You push a config that crashes the device on boot. It's now offline. What saves you?", "[pause: 2.0]"])
S(dia(K(1, "a crash loop"), "Who can fix a device that cannot connect?", "ch1-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Push a rollback.”"),
                  ("case", "Break", "The config applier applies v18 and reboots into a crash: the device never connects to hear the rollback."))), [
 P, "C: Inside the agent.", P, "C: The config applier is marked.", P, "C: The naive answer: push a rollback.", P,
 "C: But the applier applied version eighteen and rebooted into a crash loop. The device never connects long enough to hear anything."], cls="dia")
S(trace(K(1, "the trace"), "Ten thousand devices, a truck roll each", [
  ("09:00", "config v18 (display mode “eco2”) to cohort store-eu: 10,000 devices"),
  ("09:02", "hardware rev 3 has no “eco2”; the display driver crashes on boot"),
  ("09:02 →", B("crash, reboot, crash: no connection, no rollback")),
  ("09:30", B("10,000 × $150 = $1.5 M in visits"))],
  hedge=("Why the server can’t help", "Every server-side fix needs the device to connect, and that is exactly what it can no longer do.")), [
 "C: The trace.", P, "C: Nine o'clock, config eighteen to ten thousand devices in a store cohort.", P,
 "C: Hardware revision three has no such display mode, and its driver crashes on boot.", P,
 "C: Crash, reboot, crash. No connection, so no rollback.", P, "C: Ten thousand truck rolls: a million and a half dollars.", P,
 "C: Every server-side fix needs the device to connect, which is exactly what it can't do."])
S(dia(K(1, "the fix"), "The device keeps a last known good, and returns to it alone", "ch1-fix",
      extra=strip(("fixb", "Mechanism", "New configs and images are pending until confirmed: boot them with a try counter; the agent confirms only after it has reconnected and reported. Three failed boots → the bootloader restores config v17 and slot A."),
                  ("whyb", "Covers, and does not", "Crash loops, hangs, a dead network stack. Not hardware damage: a fried board needs a visit.")) + rejl(*REJ(1))), [
 P, "C: The fix.", P, "C: The bootloader.", P, "C: And the slots.", P,
 "C: One level down. A new config, like a new image, is pending until confirmed. The bootloader boots it with a try counter of three. The agent confirms only after it has reconnected and reported healthy, because a device that boots but can't talk to us is not healthy. Three failed boots, and the bootloader restores config seventeen and the image in slot A, and the device reports that it rejected eighteen.", P,
 "C: It covers crash loops, hangs and a broken network stack. Not hardware damage.", P,
 "C: Rejected: a server-side rollback command. A device that crashes on boot never connects to receive it."], cls="dia")
S(dia(K(1, "sequence"), "Three tries, then the last known good", "seq-ch1-brick"), [
 "C: As a sequence.", P, "C: Config eighteen arrives.", P, "C: Applied as pending, then a reboot to take it.", P,
 "C: The boot crashes; the watchdog resets; tries two, one, none.", P, "C: Revert to config seventeen and the firmware in slot A.", P,
 "C: And the report: rejected eighteen, crash loop. The rollout controller sees that within minutes."], cls="dia")
S(plain(K(1, "what confirms an update"), "Healthy means: still controllable", table(["Check, within 120 s of boot", "Why it is in the list"], [
  ["The application process is up", "the obvious one"],
  ["The network stack has an address", "a device that boots offline cannot be helped"],
  ["The gateway accepted our certificate", "a broken TLS library is a brick with a power light"],
  ["Desired state fetched and reported back", "an agent that cannot be updated again is the worst outcome"]], "bt sm")), [
 "C: What exactly does the agent confirm? Healthy means still controllable, so four checks within a hundred and twenty seconds of boot.", P,
 "C: The application process is up. The obvious one.", P,
 "C: The network stack has an address. A device that boots offline can't be helped.", P,
 "C: The gateway accepted our certificate. A broken T-L-S library is a brick with a power light.", P,
 "C: And desired state was fetched and reported back: a full round trip. An agent that can't be updated again is the worst possible outcome, so it's the last thing checked before the new image becomes the last known good."])

qs("Interviewer · the second-level push", "“The new firmware boots fine, but its agent has a bug: it never applies the next desired state.”", [
 "I: The new firmware boots fine, but its agent has a bug: it never applies the next desired state.", "[pause: 1.5]"])
S(plain(K(1, "the second fix"), "A kill switch below the agent", cards(
  ("grn", "Confirm means “can be updated”", "The watchdog confirmation includes a round trip: fetch desired, report it. A deaf agent never confirms."),
  ("amb", "A separate, signed path", "A tiny recovery client in the bootloader polls one signed URL daily: “revert to slot A”."),
  ("red", "Honest limit", "A bug that passes both checks and only fails later needs the next release; waves keep it small."), cols=3)), [
 P, "C: First, confirming means the device can still be updated: the confirmation needs a full round trip, fetching desired state and reporting it. A deaf agent never confirms, so it reverts.", P,
 "C: Second, a kill switch below the agent: a tiny recovery client in the bootloader polls one signed U-R-L once a day, and acts on revert to slot A.", P,
 "C: The honest limit: a bug that passes both and fails later needs the next release. That's why releases go in waves."])
say_slide("“I'd never rely on a server to rescue a device. New configs and images are pending until the agent confirms, after a full round trip to us, within a watchdog deadline. Three failed boots and the bootloader returns to the last known good on its own; a signed recovery path sits below the agent.”", [
 "V: If asked, I'd say: I'd never rely on a server to rescue a device. New configs and images are pending until the agent confirms, after a full round trip to us, within a watchdog deadline. Three failed boots and the bootloader returns to the last known good on its own, and a signed recovery path sits below the agent.", "[pause: 1.0]",
 "N: That fix creates the next question: the device recovers. How many devices have to go through that?"])

# ── 2
subchapter("7.2", "Challenge 2: The rare revision", ["N: Challenge two: the second half of the crux, the blast radius."])
qs("Interviewer · challenge 2 of 6", "“You release to 1 % first. It looks fine. At 10 %, one hardware revision starts bricking. What went wrong?”", [
 "I: You release to one percent first. It looks fine. At ten percent, one hardware revision starts bricking. What went wrong?", "[pause: 2.0]"])
S(dia(K(2, "a percentage"), "Is 1 % a sample?", "ch2-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“1 %, then 10 %, then everyone; someone watches the dashboard.”"),
                  ("case", "Break", "The cohort picker takes a random 1 %: hardware rev 5 is 0.3 % of the fleet, about 30 devices, all offline that day."))), [
 P, "C: Inside the rollout controller.", P, "C: The cohort picker is marked.", P, "C: The naive answer: one percent, then ten, then everyone, and someone watches.", P,
 "C: A random one percent of the fleet. Hardware revision five is point three percent of devices, so about thirty of them were in it, and that day they were offline."], cls="dia")
S(trace(K(2, "the trace"), "Thirty devices that never reported", [
  ("Mon", "wave 1: 10,000 random devices; 30 are rev 5, all offline"),
  ("Tue", "crash rate flat; a person approves 10 %"),
  ("Wed", B("100,000 devices; 300 rev 5 brick on boot (no watchdog on rev 5)")),
  ("Wed", B("300 visits: $45,000, three times the budget"))],
  hedge=("Two errors", "A sample by percentage, and a person reading a flat average.")), [
 "C: The trace.", P, "C: Monday, wave one: ten thousand random devices, thirty of them revision five, all offline.", P,
 "C: Tuesday, the crash rate is flat, and a person approves ten percent.", P,
 "C: Wednesday, three hundred revision-five devices brick. Their old bootloader has no watchdog.", P,
 "C: Three hundred visits, three times the budget.", P, "C: Two errors: a sample by percentage, and a person reading an average."])
S(dia(K(2, "the fix"), "Waves by strata, and a halt that needs no person", "ch2-fix",
      extra=strip(("fixb", "Mechanism", "Wave 1 = at least 50 online devices of every (hardware rev × region × carrier) cell. Compare each cell with its own control for 24 h; halt when a crash, reconnect or battery interval excludes zero."),
                  ("whyb", "Covers, and does not", "Rare hardware, regional networks, quiet failures. Not a failure that takes weeks: a slow leak needs the census of challenge six.")) + rejl(*REJ(2))), [
 P, "C: The fix.", P, "C: The cohort picker.", P, "C: And the halt rule.", P,
 "C: One level down. Wave one isn't a percentage; it's at least fifty online devices from every combination of hardware revision, region and carrier, chosen from devices seen in the last day. Each combination is compared with its own control group for twenty-four hours, and the halt is automatic when the interval for crashes, reconnects or battery drain excludes zero.", P,
 "C: It covers rare hardware, regional networks and quiet failures. Not a slow leak over weeks; that needs the census in challenge six.", P,
 "C: Rejected: rolling out to a percentage. One percent is mostly the most common hardware; the rare revision that bricks may not be in it at all."], cls="dia")
S(dia(K(2, "the waves"), "Every kind of device first; a person only before the big step", "waves"), [
 "C: The waves. Wave zero: a hundred internal devices. Wave one: a thousand, every hardware revision. Wave two: ten thousand, every region too. Wave three: a hundred thousand, after a person approves. Then the rest. Each soaks for a day and is compared with a control.",
 "C: And at every wave the same halt rule: if crashes, reconnects or battery are worse than the control beyond the interval, stop, and revert the wave as a new version of desired state. The person approves going faster. Nobody has to approve stopping."], cls="dia")
S(plain(K(2, "what a wave can see"), "A thousand devices, and a failure that matters", table(["Failure rate a day", "Expected in 1,000", "Seen in a day?"], [
  ["0.2 % (normal crashes)", "2", "the baseline"],
  ["1 % (5×)", "10", "yes: the interval excludes the baseline"],
  ["0.3 % (1.5×)", "3", "no: needs 10,000 devices or a week"],
  ["Bricking, any rate", "devices that never report", "yes: watchdog reverts and silence are counted"]], "bt sm")), [
 "C: What a thousand-device wave can actually see.", P, "C: Normal crashes at point two percent a day: about two in a thousand. That's the baseline.", P,
 "C: A five-times regression: ten crashes against two expected. A day's soak sees it.", P,
 "C: A one-and-a-half-times regression: three against two. Invisible at a thousand; it needs ten thousand devices or a week. That's what wave two is for.", P,
 "C: And bricking at any rate is visible, because the halt counts watchdog reverts and devices that stop reporting, not only crashes."])

qs("Interviewer · the second-level push", "“Halts keep firing on noise, and releases take six weeks.”", ["I: Halts keep firing on noise, and releases take six weeks.", "[pause: 1.5]"])
S(plain(K(2, "the second fix"), "Tune the test, not the courage", cards(
  ("grn", "Intervals, not thresholds", "Halt only when the interval excludes zero; more devices per cell narrows it."),
  ("amb", "Halt, then look", "A halt pauses; a person can resume with a reason, recorded with the release."), cols=2)), [
 P, "C: Halt on intervals, not thresholds, and put more devices per cell to narrow them. Noise stops firing.", P,
 "C: And a halt pauses rather than kills. A person can resume with a recorded reason. False halts cost a day; a missed real one costs a fleet."])
say_slide("“A percentage isn't a sample. Wave one has every hardware revision, region and carrier in it, each compared with its own control for a day, and the halt is automatic when an interval excludes zero. A person approves going faster; nobody needs to approve stopping.”", [
 "V: If asked, I'd say: a percentage isn't a sample. Wave one has every hardware revision, region and carrier in it, each compared with its own control for a day, and the halt is automatic when an interval excludes zero. A person approves going faster; nobody needs to approve stopping.", "[pause: 1.0]",
 "N: That fix creates the next question: the waves assume devices are online. Many aren't."])

# ── 3
subchapter("7.3", "Challenge 3: Six weeks offline", ["N: Challenge three: the device that comes back."])
qs("Interviewer · challenge 3 of 6", "“A device has been offline for six weeks, and four config changes happened. What does it do when it reconnects?”", [
 "I: A device has been offline for six weeks, and four config changes happened. What does it do when it reconnects?", "[pause: 2.0]"])
S(dia(K(3, "a returning device"), "Replay the history, or jump to now?", "ch3-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Queue the four changes and deliver them in order.”"),
                  ("case", "Break", "The config applier works through v15, v16, v17, v18: three obsolete states, one incompatible."))), [
 P, "C: Inside the agent.", P, "C: The config applier is marked.", P, "C: The naive answer: queue the four changes, deliver them in order.", P,
 "C: Then the applier works through fifteen, sixteen and seventeen to reach eighteen: three obsolete states, and one of them needs firmware the device doesn't have."], cls="dia")
S(trace(K(3, "the trace"), "Four changes, one of them impossible", [
  ("Week 0", "device d-7781 on firmware 4.0, config v14, goes offline"),
  ("Weeks 1–5", "v15, v16 (needs firmware 4.1), v17, v18 published"),
  ("Week 6", "d-7781 reconnects; a queue delivers v15 … v18"),
  ("Week 6", B("v16 fails on 4.0; the queue blocks; v17 and v18 never apply"))],
  hedge=("What it needed", "One document: the latest desired state, and whatever firmware it requires first.")), [
 "C: The trace.", P, "C: Week zero, a device on firmware four point zero, config fourteen, goes offline.", P,
 "C: Over five weeks, four configs; one needs firmware four point one.", P, "C: In week six it reconnects, and a queue delivers fifteen through eighteen.", P,
 "C: Sixteen fails on the old firmware, the queue blocks, and seventeen and eighteen never apply.", P,
 "C: What it needed was one document: the latest desired state, and the firmware that requires."])
S(dia(K(3, "the fix"), "Latest wins; prerequisites first", "ch3-fix",
      extra=strip(("fixb", "Mechanism", "The device reads one desired document (v18). If v18 needs firmware ≥ 4.1, the reconciler serves the firmware step first, then v18. Applying is idempotent: the same version twice is a no-op."),
                  ("whyb", "Covers, and does not", "Any absence, any number of changes. Not configs that must be applied in sequence: those are migrations, owned by firmware.")) + rejl(*REJ(3))), [
 P, "C: The fix.", P, "C: The config applier.", P,
 "C: One level down. The device reads one desired document, version eighteen, and applies the whole of it. If eighteen needs firmware four point one or later, the reconciler serves the firmware step first, through the normal wave the device belongs to, then eighteen. Applying the same version twice is a no-op, so a nudge sent twice does nothing.", P,
 "C: It covers any absence and any number of changes. Not changes that must happen in sequence; those are migrations, and the firmware owns them.", P,
 "C: Rejected: replaying every queued change in order. A device offline for six weeks applies four obsolete configs to reach the fifth."], cls="dia")
S(plain(K(3, "the agent's loop, as pseudocode"), "Level-triggered: compare, then converge",
  pseudo("loop every connect and every 6 h:\n    d = get_desired()                  # one document\n    if d.version == applied.version: continue\n    if fw < d.min_firmware:\n        report(blocked_on = d.min_firmware); continue\n    stage(d); reboot_if_needed()\n    if healthy_round_trip(): confirm(d)\n    else: revert(applied)              # last known good", hl=(2, 4, 7))), [
 "C: The agent's loop, level-triggered. Line two: one document, the latest. Line four: if it needs newer firmware, report what it's blocked on, and wait for the firmware wave. Line seven: confirm only after a healthy round trip, otherwise revert. Nothing in the loop depends on what happened while it was away."])
qs("Interviewer · the second-level push", "“The device's clock is wrong after six weeks without power.”", ["I: The device's clock is wrong after six weeks without power.", "[pause: 1.5]"])
S(plain(K(3, "the second fix"), "Versions, not times", cards(
  ("grn", "Order by version", "Desired and reported documents compare versions; no decision reads the device's clock."),
  ("amb", "Time from the server", "The gateway stamps receipt time; certificates are checked against it, with a grace window."), cols=2)), [
 P, "C: Nothing compares times. Desired and reported state compare versions, so a clock in nineteen seventy changes no decision.", P,
 "C: And the gateway stamps receipt time from its own clock, with a grace window for certificate validity, so a device with a dead clock can still connect and fix it."])
say_slide("“A device never replays history. It reads one desired document, the latest, applies all of it, and reports the version. If that needs newer firmware, it reports what it's blocked on and the firmware wave comes first. Versions order everything; the device's clock orders nothing.”", [
 "V: If asked, I'd say: a device never replays history. It reads one desired document, the latest, applies all of it, and reports the version. If that needs newer firmware, it reports what it's blocked on, and the firmware wave comes first. Versions order everything; the device's clock orders nothing.", "[pause: 1.0]",
 "N: That fix creates the next question: what if a lot of devices come back at once?"])
