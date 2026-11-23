from dsl import *
from stack import REJ
P = "[+]"
B = lambda x: f'<span class="bad">{x}</span>'
K = lambda n, t: f"Challenge {n} of 6 · {t}"

# ── 4
subchapter("7.4", "Challenge 4: The reconnect storm", ["N: Challenge four: overload, caused by the fleet recovering."])
qs("Interviewer · challenge 4 of 6", "“A regional ISP comes back, and 200,000 devices reconnect in the same minute. What happens to your control plane?”", [
 "I: A regional internet provider comes back, and two hundred thousand devices reconnect in the same minute. What happens to your control plane?", "[pause: 2.0]"])
S(dia(K(4, "a storm"), "Who decides how fast devices come back?", "ch4-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Brokers autoscale.”"),
                  ("case", "Break", "Admission accepts everyone at once: 40,000 TLS handshakes a second, timeouts, and every device retries in step."))), [
 P, "C: Inside the gateway.", P, "C: Admission is marked.", P, "C: The naive answer: brokers autoscale.", P,
 "C: Autoscaling takes minutes. Admission accepts everyone at once: forty thousand T-L-S handshakes a second, timeouts, and every device retries on the same fixed schedule."], cls="dia")
S(trace(K(4, "the trace"), "A storm that keeps itself going", [
  ("14:00:00", "the ISP recovers; 200,000 devices try to connect"),
  ("14:00:05", "40,000 handshakes/s; brokers at 100 % CPU; half time out"),
  ("14:00:15", B("every device retries after exactly 10 s: the same storm again")),
  ("14:20", B("still down: retries in lockstep are the load"))],
  hedge=("Metastable", "The cause ended at 14:00. The retries are now the outage.")), [
 "C: The trace.", P, "C: At two, the provider recovers and two hundred thousand devices try to connect.", P,
 "C: Five seconds in, forty thousand handshakes a second; brokers saturate; half time out.", P,
 "C: Every device retries after exactly ten seconds: the same storm again.", P, "C: Twenty minutes later it's still down.", P,
 "C: The cause ended at two o'clock. The retries are now the outage."])
S(dia(K(4, "the fix"), "Spread the arrivals; admit at the rate you can serve", "ch4-fix",
      extra=strip(("fixb", "Mechanism", "Devices back off with full jitter: wait random(0, min(cap, base × 2ⁿ)). Each node admits through a token bucket (2,000 connects/s) and refuses the rest with a retry-after. A current device’s desired read is one version compare in cache."),
                  ("whyb", "Covers, and does not", "Storms after outages, deploys and power cuts. Not a slow broker: that is capacity.")) + rejl(*REJ(4))), [
 P, "C: The fix.", P, "C: Admission.", P, "C: And the desired-state cache.", P,
 "C: One level down. Devices back off with full jitter: wait a random time between zero and a cap that doubles with each failure, so retries spread out instead of lining up. Each node admits through a token bucket, two thousand connections a second, and refuses the rest with a retry-after hint the agent honours. And a device that's already current costs one version comparison in the cache, not a database read.", P,
 "C: It covers storms after outages, deploys and power cuts. Not a broker that's simply too small.", P,
 "C: Rejected: immediate reconnect with a fixed retry. Two hundred thousand devices retry in step, and the brokers never recover."], cls="dia")
S(plain(K(4, "what jitter buys"), "Two hundred thousand devices, spread over the window", table(["Retry policy", "Peak connects per second", "Brokers"], [
  ["Fixed 10 s, everyone", "≈ 40,000, again every 10 s", "never recover"],
  ["Exponential, no jitter", "40,000 at 2 s, 4 s, 8 s … in waves", "recover slowly, after many storms"],
  ("pick", ["<b>Full jitter, cap 15 min</b>", "≈ 200,000 ÷ 900 s ≈ <b>220/s</b> at the tail", "well inside 20 × 2,000/s"])], "bt sm")), [
 "C: What jitter buys, in numbers.", P,
 "C: A fixed ten-second retry: forty thousand connects a second, again every ten seconds. The brokers never recover.", P,
 "C: Exponential backoff without jitter still sends everyone at two seconds, four, eight: the storms get rarer, not smaller.", P,
 "C: Full jitter with a fifteen-minute cap spreads two hundred thousand devices across the window: by the tail, around two hundred and twenty a second, far inside twenty nodes at two thousand each. Devices come back over minutes, and the control plane stays up the whole time."])

S(plain(K(4, "the agent's backoff, as pseudocode"), "Random, growing, and obedient",
  pseudo("attempt = 0\nwhile not connected:\n    cap = min(15 min, 2 s * 2 ** attempt)\n    sleep(random(0, cap))              # full jitter\n    r = connect()\n    if r.retry_after:\n        sleep(r.retry_after + random(0, 30 s))\n    attempt += 1\non connected: attempt = 0", hl=(3, 4, 7))), [
 "C: The backoff in pseudocode. Line three: a cap that doubles, up to fifteen minutes. Line four: sleep a random fraction of it, the full jitter, so two hundred thousand devices spread over the window. Line six: if the broker says retry after, obey it, with a little jitter of its own."])
qs("Interviewer · the second-level push", "“The devices that reconnect all ask for desired state, and the shadow database melts.”", [
 "I: The devices that reconnect all ask for desired state, and the shadow database melts.", "[pause: 1.5]"])
S(plain(K(4, "the second fix"), "Most devices are already current", cards(
  ("grn", "Version first", "A reconnecting device sends its applied version; the gateway compares it with a cached per-cohort version and answers “current”."),
  ("amb", "The database for the rest", "Only devices behind read their document: after a short outage, nearly none."), cols=2)), [
 P, "C: Most reconnecting devices are already current. The device sends its applied version, the gateway compares it with a cached version per cohort, and answers current.", P,
 "C: Only devices that are actually behind read their document from the database. After a short outage, that's almost none."])
say_slide("“A recovering fleet must not become the next outage. Devices back off with full jitter and obey a retry-after; each broker admits through a token bucket; and a reconnecting device that's already current costs one cached version compare, not a database read.”", [
 "V: If asked, I'd say: a recovering fleet must not become the next outage. Devices back off with full jitter and obey a retry-after, each broker admits through a token bucket, and a reconnecting device that's already current costs one cached version compare, not a database read.", "[pause: 1.0]",
 "N: That fix creates the next question: those devices also bring weeks of buffered telemetry."])

# ── 5
subchapter("7.5", "Challenge 5: Telemetry, twice", ["N: Challenge five: the health signals the rollout decides on."])
qs("Interviewer · challenge 5 of 6", "“Devices buffer health reports while offline and send them on reconnect. Some arrive twice. And someone labels the crash metric by device ID. What happens to your rollout decisions?”", [
 "I: Devices buffer health reports while offline and send them on reconnect. Some arrive twice. And someone labels the crash metric by device I-D. What happens to your rollout decisions?", "[pause: 2.0]"])
S(dia(K(5, "duplicates"), "What makes a report a repeat?", "ch5-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“MQTT QoS 2 delivers exactly once.”"),
                  ("case", "Break", "The buffer resends after a reboot: a new session, so the broker sees new messages. Crashes counted twice."))), [
 P, "C: Inside the agent.", P, "C: The telemetry buffer is marked.", P, "C: The naive answer: MQTT's highest quality of service delivers exactly once.", P,
 "C: Within one session. The buffer resends after a reboot, which is a new session, so the crash reports count twice."], cls="dia")
S(trace(K(5, "the trace"), "A wave that looks twice as bad", [
  ("Tue", "wave 2 devices crash once each overnight, normal rate"),
  ("Wed 06:00", "they reconnect and flush; half flush twice after a reboot mid-upload"),
  ("Wed 06:10", B("wave crash rate 1.5× control: the halt fires on duplicates")),
  ("Wed", B("and a device-ID label made 1 M series: the metrics store slows to minutes"))],
  hedge=("Two errors", "Duplicates that look like failures, and labels that make the signal unreadable.")), [
 "C: The trace.", P, "C: Tuesday night, wave-two devices crash once each: the normal rate.", P,
 "C: Wednesday morning they flush their buffers, and half flush twice after rebooting mid-upload.", P,
 "C: The wave's crash rate looks one and a half times the control, and the halt fires on duplicates.", P,
 "C: And the device-I-D label made a million series, so the metrics store answers in minutes.", P,
 "C: Duplicates that look like failures, and labels that make the signal unreadable."])
S(dia(K(5, "the fix"), "A sequence per device; labels per cohort", "ch5-fix",
      extra=strip(("fixb", "Mechanism", "Each report carries (device, seq) from a counter in flash. The consumer keeps the last seq per device (1 M entries) and drops anything not newer. Metrics carry cohort, firmware and wave; device IDs go to the lake."),
                  ("whyb", "Covers, and does not", "Resends across sessions and reboots. Not a device whose flash was wiped: its seq restarts with a new epoch.")) + rejl(*REJ(5))), [
 P, "C: The fix.", P, "C: The telemetry buffer.", P,
 "C: One level down. Each report carries the device I-D and a sequence number from a counter kept in flash, so it survives reboots. The consumer keeps the last sequence per device, a million entries, and drops anything not newer. Metrics carry cohort, firmware and wave labels; per-device data goes to the lake, where it's a row, not a series.", P,
 "C: It covers resends across sessions and reboots. Not a device whose flash was wiped: its counter restarts with a new epoch number in front.", P,
 "C: Rejected: exactly-once from the broker. Its highest quality of service covers one session; a device replaying its buffer after a reboot is a new session."], cls="dia")
S(plain(K(5, "the consumer, as pseudocode"), "Drop repeats, then aggregate by cohort",
  pseudo("on report(dev, epoch, seq, body):\n    last = seen.get(dev)                # (epoch, seq)\n    if last and (epoch, seq) <= last: return\n    seen[dev] = (epoch, seq)\n    m = labels(cohort(dev), body.fw, wave(dev))\n    counters[m].add(body.crashes, body.reconnects)\n    lake.append(dev, epoch, seq, body)  # per device", hl=(3, 5, 7))), [
 "C: The consumer in pseudocode. Line three: anything not newer than the last epoch and sequence for this device is dropped. Line five: the labels are cohort, firmware and wave, never the device. Line seven: the per-device record goes to the lake, for the engineer who needs one device's story."])
qs("Interviewer · the second-level push", "“A wave of a thousand devices: is a crash rate of 0.3 % against 0.2 % real?”", [
 "I: A wave of a thousand devices. Is a crash rate of point three percent against point two real?", "[pause: 1.5]"])
S(plain(K(5, "the second fix, and the honest limit"), "Small waves need patient statistics", cards(
  ("grn", "Count, don’t guess", "3 crashes against 2 expected is noise; the interval says so. Soak longer, or widen the cell."),
  ("amb", "Leading signals", "Reconnects and watchdog reverts move before crashes; halt on those too."),
  ("red", "Honest limit", "A failure rarer than 1 in 1,000 a day is invisible in wave 1; that is what waves 2 and 3 are for."), cols=3)), [
 P, "C: Count, don't guess. Three crashes against two expected is noise, and the interval says so. Soak longer or widen the cell.", P,
 "C: Use leading signals: reconnects and watchdog reverts move before crashes do.", P,
 "C: And the honest limit: a failure rarer than one in a thousand a day can't be seen in a thousand devices. That's what the bigger waves are for."])
say_slide("“Telemetry decides rollouts, so it must be right. Every report carries a device sequence from flash, the consumer drops anything not newer, and metrics are labelled by cohort, firmware and wave, never by device, which goes to the lake instead.”", [
 "V: If asked, I'd say: telemetry decides rollouts, so it must be right. Every report carries a device sequence from flash, the consumer drops anything not newer, and metrics are labelled by cohort, firmware and wave, never by device. Per-device data goes to the lake instead.", "[pause: 1.0]",
 "N: That fix creates the last question: how would you know the fleet is actually where you think it is?"])

# ── 6
subchapter("7.6", "Challenge 6: Connected is not converged", ["N: Challenge six is observability of a fleet, not of servers."])
qs("Interviewer · challenge 6 of 6", "“The dashboard says 98 % of devices are connected and healthy. A customer says their devices still run last year's firmware. How would you have known?”", [
 "I: The dashboard says ninety-eight percent of devices are connected and healthy. A customer says their devices still run last year's firmware. How would you have known?", "[pause: 2.0]"])
S(dia(K(6, "a quiet fleet"), "What does “healthy” leave out?", "ch6-attack", q=True, red=True,
      extra=strip(("case", "Naive answer", "“Connected devices: 98 %.”"),
                  ("case", "Break", "The metrics store counts connections; nothing compares reported state with desired."))), [
 P, "C: The gateway, telemetry, metrics and the shadow store.", P, "C: The metrics store is marked.", P,
 "C: The naive answer: ninety-eight percent connected.", P,
 "C: The metrics count connections. Nothing compares what devices report with what we told them to be."], cls="dia")
S(trace(K(6, "the trace"), "Connected, healthy, and nine months behind", [
  ("March", "release 4.1 to everyone"),
  ("March", "cohort “retail-us” on old bootloaders reports “blocked on 4.0.9”"),
  ("March – Dec", B("connected, sending health, never converging: no alert")),
  ("December", B("the customer notices before we do"))],
  hedge=("What the dashboards saw", "Connected and healthy: true, and beside the point.")), [
 "C: The trace.", P, "C: March, release four point one to everyone.", P,
 "C: One retail cohort, on old bootloaders, reports blocked on a prerequisite version.", P,
 "C: For nine months it's connected, sends health, and never converges. No alert.", P,
 "C: In December the customer notices first.", P, "C: Connected and healthy: true, and beside the point."])
S(dia(K(6, "the fix"), "Version four: a fleet census", "base-v4", vtag="V4"), [
 P, "C: The fix changes the design: version four. Version three, carried.", P,
 "C: New: a fleet census, reading the shadow store and the metrics, every hour."], cls="dia")
S(plain(K(6, "the fix, one level down"), "Measure convergence, not connection", cards(
  ("grn", "Census", "Devices by (firmware, config, cohort, hardware rev): the version tail, every hour."),
  ("grn", "Convergence", "Time from a desired change to 95 % of online devices reporting it."),
  ("grn", "Blocked and rejected", "Devices reporting “blocked on” or “rejected v”, by cohort."),
  ("grn", "Unseen", "Devices not seen for 7, 30, 90 days: lost, stolen, or in a drawer."), cols=2) + rejl(*REJ(6))), [
 "C: One level down, four measures.", P, "C: A census: devices by firmware, config, cohort and hardware, every hour. The version tail is a table, not a guess.", P,
 "C: Convergence: from a desired change to ninety-five percent of online devices reporting it. Ours stalled at ninety-four for nine months.", P,
 "C: Blocked and rejected: devices reporting blocked on, or rejected, by cohort. That one would have fired in March.", P,
 "C: Unseen: devices not seen for seven, thirty or ninety days. Lost, stolen, or in a drawer.", P,
 "C: Rejected: dashboards of connected devices. A device that connects but runs the wrong firmware looks exactly healthy."])
S(plain(K(6, "reading the signals"), "Symptoms in pairs", table(["Symptom", "Paired with", "Means"], [
  ["Convergence stalls", "“blocked on” rising", "a prerequisite missing: serve the firmware step"],
  ["Convergence stalls", "“rejected” rising", "the change fails on some hardware: halt it"],
  ["Reconnects up", "one wave only", "the release, not the network"],
  ["Reconnects up", "every wave, one carrier", "the network, not us"],
  ["Watchdog reverts", "one hardware rev", "a driver bug: halt that cell"]], "bt sm")), [
 "C: And read them in pairs.", P, "C: Convergence stalls with blocked-on rising: a missing prerequisite. Serve the firmware step.", P,
 "C: Convergence stalls with rejections rising: the change fails on some hardware. Halt it.", P,
 "C: Reconnects up in one wave only: the release. In every wave on one carrier: the network.", P,
 "C: The same pair, the other way round: every wave, one carrier, means the carrier, and the release can continue.", P,
 "C: And watchdog reverts on one hardware revision: a driver bug. Halt that cell."])
S(plain(K(6, "the SLIs"), "What the fleet promises, measured", table(["SLI", "Target"], [
  ["Online devices on the desired config within 24 h", "≥ 95 %"],
  ["Devices harmed per release", "≤ 100"],
  ["Watchdog reverts per release", "measured, alerted per cell"],
  ["Devices unseen for 30 days", "watched; contract-dependent"],
  ["Control-plane availability", "99.9 %; devices run without it"]], "bt sm")), [
 "C: And the fleet's service levels.", P, "C: Online devices on the desired config within a day: at least ninety-five percent.", P,
 "C: Devices harmed per release: at most a hundred.", P, "C: Watchdog reverts: measured and alerted per cell.", P,
 "C: Devices unseen for thirty days: watched, against the customer's contract.", P,
 "C: And the control plane at three nines, because devices keep running without it."])
say_slide("“I'd watch convergence, not connection: an hourly census by firmware, config, cohort and hardware; the time for a change to reach 95 % of online devices; devices reporting blocked or rejected; and devices we haven't seen in weeks. Connected and healthy can be true for a device that's nine months behind.”", [
 "V: If asked, I'd say: I'd watch convergence, not connection. An hourly census by firmware, config, cohort and hardware; the time for a change to reach ninety-five percent of online devices; devices reporting blocked or rejected; and devices we haven't seen in weeks. Connected and healthy can be true for a device that's nine months behind.", "[pause: 1.0]"])

chapter(8, "Recap", 6, "The final design, and what to say", ["C: The recap."])
S(dia("Recap · version four", "Where each mechanism ended up", "recap"), [
 P, "C: Version four.", P, "C: The agent: A-B slots and the watchdog.", P, "C: The gateway: identity per device, and admission with backoff.", P,
 "C: The shadow store: desired and reported.", P, "C: The reconciler: convergence, gently.", P, "C: The rollout controller: waves by cohort that halt themselves.", P,
 "C: And the census, which tells us where the fleet really is."], cls="dia")
S(plain("Recap · one sentence per path", "Four paths, four sentences", cards(
  ("", "Know", "Devices report versions and health; health is aggregated by cohort, deduplicated by sequence."),
  ("grn", "Configure", "An operator writes a versioned desired document; devices converge to the latest when they can."),
  ("amb", "Release", "Signed images, waves by cohort, each compared with a control; a halt needs no person."),
  ("red", "Stop", "Devices revert on their own; the controller reverts desired state as a new version."), cols=2)), [
 "C: One sentence per path.", P, "C: Know: devices report versions and health, aggregated by cohort and deduplicated by sequence.", P,
 "C: Configure: an operator writes a versioned desired document, and devices converge to the latest when they can.", P,
 "C: Release: signed images, waves by cohort, each compared with a control, and a halt that needs no person.", P,
 "C: Stop: devices revert on their own, and the controller reverts desired state as a new version."])
S(plain("Recap · the mistakes", "What costs most in this round", table(["Mistake", "Instead"], [
  ["Commands pushed to online devices", "desired state, pulled and reconciled"],
  ["A server-side rollback for a crash loop", "A/B slots, a watchdog, a last known good"],
  ["Rolling out to a percentage", "waves by strata, with an automatic halt"],
  ["Replaying queued changes", "latest wins; prerequisites first"],
  ["Immediate, fixed retries", "full jitter, admission control"],
  ["Counting connected devices", "a census and convergence time"]], "bt sm")), [
 "N: The mistakes that cost most.", P, "N: Commands pushed to online devices. Instead, desired state, pulled and reconciled.", P,
 "N: A server-side rollback for a crash loop. Instead, A-B slots and a watchdog.", P,
 "N: Rolling out to a percentage. Instead, strata and an automatic halt.", P, "N: Replaying queued changes. Instead, latest wins.", P,
 "N: Immediate, fixed retries. Instead, full jitter and admission control.", P, "N: Counting connected devices. Instead, a census and convergence time."])
key("The close", "Publish a <em>desired state</em>, never a command; release in <em>waves that halt themselves</em>; and let every device <em>return to its last known good</em> without help.", [
 "V: Publish a desired state, never a command. Release in waves that halt themselves. And let every device return to its last known good without help.", "[pause: 1.0]",
 "C: Thanks for watching. The written design is linked below."])
