from dsl import *
from stack import TECH, STACK, SUMMARY, SUMMARY_SAY, say_text
import re
P = "[+]"

chapter(4, "API and entities", 3, "What a device and an operator exchange", ["C: The interfaces, then the data."])

S(plain("API · the desired document (FR2, FR3)", "What a device pulls: the whole state, with a version",
  chips("serves FR2, FR3", "reads DESIRED", "a device applies all of it") +
  code('GET devices/d-7781/desired   (MQTT, retained)\n{"version": 18,\n "config": {"display": "eco", "report_s": 300},\n "firmware": {"version": "4.3",\n   "url": "https://cdn…/fw-4.3-hw2.bin",\n   "sha256": "9f1c…", "signature": "MEQC…"},\n "min_firmware_for_config": "4.1"}', "json", hl=(2, 6, 7))), [
 "C: The desired document a device pulls, for F-R-two and three. It's the whole state, with a version, not a command.",
 "C: Three lines matter. The version, so a device knows whether it's current. The image's hash and offline signature, which the device checks before writing anything. And the minimum firmware the configuration needs, so a device on an old image doesn't apply a config it can't run."])

S(plain("API · the reported document (FR1)", "What a device says it is, including what it refused",
  code('PUBLISH devices/d-7781/reported   (MQTT, QoS 1)\n{"version": 18, "firmware": "4.3", "slot": "B",\n "config_applied": 18,\n "rejected": [{"version": 17, "reason": "crash_loop"}],\n "blocked_on": null,\n "seq": 88120, "epoch": 3}', "json", hl=(3, 4, 6))), [
 "C: The reported document, for F-R-one. What the device runs: version, firmware and active slot.",
 "C: The lines that matter. The config it applied. What it rejected, and why, which is how the rollout controller learns about a crash loop it could never see. And a sequence and epoch, so a resend is recognised as one."])

S(plain("API · the rest", "Three more, each tagged", table(["Interface", "Serves", "Touches", "Carries"], [
  ["<code>devices/{id}/reported</code> (MQTT, device → us)", "FR1", "REPORTED", "versions applied, firmware, rejected changes"],
  ["<code>PUT /v1/cohorts/{c}/desired</code> (operator)", "FR2", "DESIRED", "a document, <code>If-Match: v17</code>"],
  ["<code>POST /v1/releases</code> {image, waves}", "FR3, FR4", "RELEASE, WAVE", "the plan; halts happen without a call"]], "bt xs mx")), [
 "C: Three more.", P, "C: Reported state, from each device: what it applied, what it runs, and what it rejected.", P,
 "C: Desired state for a cohort, from an operator, with if-match on the version, so two operators can't overwrite each other.", P,
 "C: And a release: an image and a wave plan. Halting doesn't need a call; the controller does it."])

S(dia("Data · conceptual model", "Devices in cohorts; desired and reported, versioned", "erd-chen"), [
 "C: The conceptual model.", P, "C: A device, with its hardware revision.", P, "C: In a cohort.", P,
 "C: A device wants a desired document: a weak entity, identified by the device and a version.", P,
 "C: And reports a reported document, also versioned.", P, "C: Releases target cohorts.", P, "C: And ship one signed image."], cls="dia")

S(dia("Data · physical model", "One row per device; history beside it", "erd-physical"), [
 "C: The physical tables.", P, "C: Device: cohort, hardware revision, desired and reported versions. Drift is desired version greater than reported.", P,
 "C: Desired documents, append-only, so a rollback is writing an old document as a new version.", P,
 "C: Releases, owned by the rollout controller.", P, "C: Waves: soak, compare, continue or halt.", P,
 "C: Reported documents, including what the device rejected.", P, "C: And telemetry in the time-series store, labelled by cohort, never by device."], cls="dia")

chapter(5, "High-level design", 4, "Three versions on one picture, then every path", ["C: The design in three versions, on one picture that only changes by deltas."])

S(dia("Design · version 1", "The simplest thing that works: a shadow behind a broker", "base-v1", vtag="V1"), [
 "C: Version one.", P, "C: A device agent on every device.", P, "C: Connected to a device gateway, an MQTT broker, over mutual T-L-S.", P,
 "C: Reported state lands in a shadow store; desired state is read from it.", P, "C: A fleet A-P-I writes desired state.", P,
 "C: For operators. The objection: a device offline when the change happens only gets it if it asks, and nothing tells us how healthy anything is."], cls="dia")

S(dia("Design · version 2", "Convergence and health: a reconciler and telemetry", "base-v2", vtag="V2"), [
 "C: Version two.", P, "C: Version one, carried.", P, "C: New, a reconciler: it finds devices whose reported version lags, and nudges them.", P,
 "C: New, telemetry: health summaries every five minutes.", P,
 "C: New, a metrics store, labelled by cohort. The objection: a firmware release still goes to everyone at once."], cls="dia")

S(dia("Design · version 3", "Releases: a controller of waves, and signed images on a CDN", "base-v3", vtag="V3"), [
 "C: Version three.", P, "C: Version two, carried.", P,
 "C: New, a rollout controller: it writes desired firmware wave by wave, and reads each wave's health against a control.", P,
 "C: New, an image C-D-N: devices fetch signed images there, never through the brokers. This is the baseline."], cls="dia")

S(plain("Design · the containers", "Each container, what it owns, and its number", table(["Container", "Owns", "Its number"], [
  ["Device agent", "Applying the whole state; A/B slots; the watchdog", "1 M devices"],
  ["Device gateway", "Sessions, identity, desired-state reads", "20 nodes"],
  ["Shadow store", "Desired and reported, versioned", "4 GB"],
  ["Reconciler", "Finding and nudging drift, gently", "40,000 nudges per change"],
  ["Rollout controller", "Waves, soak, compare, halt", "a release in ~2 weeks"],
  ["Telemetry + metrics", "Health by cohort", "3,300 reports/s"]], "bt xs mx")), [
 "C: The containers.", P, "C: The device agent: applying the whole state, the A-B slots and the watchdog. A million of them.", P,
 "C: The gateway: sessions, identity, and desired-state reads. Twenty nodes.", P, "C: The shadow store: desired and reported, versioned. Four gigabytes.", P,
 "C: The reconciler: finds drift and nudges it, gently, spread over minutes.", P,
 "C: The rollout controller: waves, soak, compare, halt.", P, "C: And telemetry and metrics: health, by cohort."])

S(dia("Flow · FR2", "A config, from the operator to the device", "flow-config"), [
 P, "C: A configuration change, numbered.", P, "C: One: the operator changes it.", P, "C: Two: the A-P-I writes desired version eighteen, if seventeen.", P,
 "C: Three: the reconciler finds the drift.", P, "C: Four: it nudges the gateway, spread over ten minutes.", P,
 "C: Five: the device reads desired state.", P, "C: Six: it reports version eighteen applied."], cls="dia")

S(dia("Flow · FR3", "A release, wave by wave", "flow-release"), [
 P, "C: A release, numbered.", P, "C: One: the operator starts it.", P, "C: Two: the controller writes desired firmware for wave one.", P,
 "C: Three: devices in the wave read it.", P, "C: Four: they fetch the signed image from the C-D-N.", P,
 "C: Five: they report health.", P, "C: Six: by cohort and wave.", P, "C: Seven: the controller compares the wave with the control, and continues or halts."], cls="dia")

S(dia("Sequence · FR1 know", "State and health, from one device", "seq-report"), [
 "C: Know, as a sequence.", P, "C: The agent reports: firmware four point two, config seventeen.", P,
 "C: Into the shadow, as reported version seventeen.", P, "C: Every five minutes a health summary, with a sequence number.", P,
 "C: Into Kafka, keyed by device.", P, "C: A repeated sequence is dropped. Challenge five."], cls="dia")

S(dia("Sequence · FR2 configure", "Converge, gently", "seq-config"), [
 "C: Configure, as a sequence.", P, "C: The operator writes version eighteen for a cohort, if the current one is seventeen.", P,
 "C: The reconciler finds rows where desired is ahead of reported.", P, "C: It nudges forty thousand devices, spread over ten minutes.", P,
 "C: A device asks for desired state, saying it has seventeen.", P, "C: It gets eighteen.", P,
 "C: It applies it, and if that fails, keeps seventeen.", P, "C: And reports eighteen."], cls="dia")

S(dia("Sequence · FR3 release", "One wave, soaked and compared", "seq-release"), [
 "C: Release, as a sequence.", P, "C: Wave one: a thousand devices, every hardware revision, firmware four point three.", P,
 "C: A device fetches the image by range, and verifies the signature and hash.", P,
 "C: Writes slot B, reboots into it, and has a hundred and twenty seconds to confirm health.", P,
 "C: It reports four point three, healthy.", P, "C: After a day, the wave is compared with a control.", P,
 "C: Crashes point two one percent against point two zero: the next wave."], cls="dia")

S(plain("Design · what a halt costs", "Stopping is cheap; not stopping is not", table(["Outcome", "Cost", "Who decides"], [
  ["A false halt", "a day of soak, a person reads it", "the controller halts; a person resumes"],
  ["A real halt in wave 1", "≤ 50 devices revert by themselves", "the controller"],
  ["No halt, bad release at 10 %", "up to 100,000 devices, $15 M if they brick", "nobody: that is the failure"]], "bt sm")), [
 "C: Before the stop sequence, what a halt costs, because it decides who is allowed to make it.", P,
 "C: A false halt costs a day of soak and a person reading a report. The controller halts on its own; a person resumes.", P,
 "C: A real halt in wave one costs at most fifty devices, and they revert by themselves.", P,
 "C: No halt, with a bad release at ten percent, is up to a hundred thousand devices: fifteen million dollars if they brick. So stopping never waits for a person."])

S(dia("Sequence · FR4 stop", "A halt, without anyone in the loop", "seq-halt"), [
 "C: Stop, as a sequence.", P, "C: Wave two reconnects three times as often as the control.", P,
 "C: The halt rule fires: no new devices get the release.", P, "C: Wave two's desired firmware goes back to four point two, as a new version.", P,
 "C: Devices read it.", P, "C: And slot A still holds four point two: switch and reboot. Nobody was paged to make that happen; somebody was paged to look at it."], cls="dia")

subchapter("5.1", "Components and technologies", ["C: One level down: what each box runs on, three containers opened up, and what I rejected."])

S(dia("Architecture · C4 containers · technologies", "The same containers, now with what they run on", "c4-containers-tech"), [
 P, "C: The same view, with technologies.", P, "C: The agent: C, on the device, with A-B slots and a watchdog.", P,
 "C: The gateway: an E-M-Q-X cluster speaking MQTT five over mutual T-L-S.", P, "C: The shadow store: PostgreSQL.", P,
 "C: The reconciler: a Go service.", P, "C: The rollout controller: a Go service.", P, "C: Telemetry: Kafka.", P,
 "C: Metrics: Victoria Metrics, by cohort."], cls="dia")

S(dia("Architecture · C4 components · device agent", "Inside the agent, from the network to the flash", "c4-comp-agent"), [
 "C: Inside the device agent.", P, "C: The gateway.", P, "C: The MQTT client, with jittered backoff and session resume.", P,
 "C: A kill switch on a separate, minimal path: a signed instruction it will act on even if everything else is broken.", P,
 "C: A telemetry buffer: store and forward, a sequence number per message.", P, "C: The config applier: latest version wins.", P,
 "C: The updater fetches from the C-D-N, verifies, and writes the inactive slot.", P, "C: The bootloader with its try counter.", P,
 "C: The watchdog: a hardware timer.", P, "C: And the two slots. Challenges one, three and five live here."], cls="dia")

S(dia("Architecture · C4 components · rollout controller", "Inside the controller, from a release to a halt", "c4-comp-rollout"), [
 "C: Inside the rollout controller.", P, "C: A release from the fleet A-P-I.", P, "C: The release plan: waves of point one, one, ten and a hundred percent.", P,
 "C: The cohort picker: every hardware revision, region and carrier in the early waves.", P, "C: The wave scheduler, with soak timers.", P,
 "C: An approval gate: a person before ten percent.", P, "C: The health comparer, wave against control, from the metrics store.", P,
 "C: The halt rule: stop, then revert.", P, "C: Writing the shadow store. Challenge two lives here."], cls="dia")

S(dia("Architecture · C4 components · device gateway", "Inside the gateway, from a handshake to a document", "c4-comp-gateway"), [
 "C: Inside the gateway.", P, "C: Devices.", P, "C: The T-L-S terminator checks a certificate per device.", P,
 "C: Admission control: a token bucket per node.", P, "C: Sessions that survive seven days of disconnection.", P,
 "C: A desired-state cache keyed by version: a current device costs one comparison.", P, "C: A bridge to Kafka.", P,
 "C: And the shadow store behind it. Challenge four lives here."], cls="dia")

def tsay(_id):
    s = STACK[_id]; first = lambda t: re.split(r"(?<=[.:;])\s", say_text(t))[0].rstrip(".:;") + "."
    out = [P, "C: " + say_text(s["how"]), P, "C: Why: " + first(s["why"])]
    for i, (n, w) in enumerate(s["rejected"]):
        out += [P, f"C: {'Rejected: ' if i == 0 else ''}{say_text(n)}. " + first(w)]
    return out
for _id in ("gw", "shadow", "artifact", "tele"):
    S(tech(**TECH(_id)), tsay(_id))

_ss = SUMMARY_SAY()
S(plain("Technology · the stack on one slide", "The stack, against its rivals",
        table(["Container", "Choice", "Rejected", "The deciding reason"], SUMMARY(), "bt xs mx") +
        grade("Naming a product is not the signal. Naming the property that rules out its rival is.")), _ss[:-1] + [P, _ss[-1]])

subchapter("5.2", "When you don't need all this", ["C: Before I break it: a small fleet needs much less."], sub="ALTERNATE")

S(dia("Alternate path · ALTERNATE", "No reconciler, no controller: a managed device service", "alt",
      extra=strip(("fixb", "How it works", "A managed IoT service holds the device shadows; devices poll desired state hourly; releases are three manual steps (1 %, 10 %, all) watched by a person."),
                  ("case", "What it gives up", "Automatic halts, cohort strata, and convergence measured rather than hoped."))), [
 P, "C: The alternate path, on version three.", P, "C: The reconciler goes.", P, "C: And the rollout controller.", P,
 "C: Instead, a managed I-o-T service holds the shadows, devices poll desired state hourly, and a release is three manual steps watched by a person.", P,
 "C: What it gives up: automatic halts, cohorts built from strata, and convergence measured rather than hoped for. The A-B slots and the watchdog stay: those I'd never skip."], cls="dia")

key("ALTERNATE · the line", "Bricking 1 % of <em>5,000 devices</em> is 50 visits, $7,500. Of a <em>million</em>, $1.5 M. Below about <em>10,000 devices</em>, I'd ship the managed service and manual waves.", [
 "C: Where's the line? Bricking one percent of five thousand devices is fifty truck rolls, seven and a half thousand dollars. Of a million, a million and a half.",
 "V: Below about ten thousand devices, I'd ship a managed service and manual waves, and keep the A-B slots and the watchdog no matter what.", "[pause: 0.8]"])
