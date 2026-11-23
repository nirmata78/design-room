# SD-29 · Device-fleet control plane (IoT) — reference-solution video outline

Target level: staff · **Compact cut** (GUIDELINES §3.4): ≈ 60 min, ≈ 6,800 words, 6 challenges, no build-cost chapter, no drill.

## Thesis and definition

- **Thesis:** never send a device a command; publish a desired state it converges to whenever it can. Release in waves that halt
  themselves, and give every device a last known good it returns to on its own.
- **Definition:** keeping a million unreachable, untrusted devices converging to a desired state, safely.
- **Hook:** move fast and a bad image bricks a million devices ($150 M at $150 a truck roll); move never and seven years of devices
  run unpatched; move in waves that start with every kind of hardware and stop themselves.

## Scale line (GUIDELINES §3.1)

Volume per month: **one firmware release and ~30 config changes; ~8.6 B health reports** · Total: **1 M devices, 7 years in the
field** · Peak: **200,000 devices reconnect in one minute** after a regional ISP outage.

## 0 · What this question grades

| Axis | Weak | Strong |
|---|---|---|
| Requirements | "push updates" | how often offline; what a bricked device costs |
| Correctness | commands to online devices | desired vs reported, reconciled; latest wins |
| Safety | percentage rollouts watched by a person | cohorts, automatic halt, A/B + watchdog |
| Depth | "use MQTT" | per-device identity, signed images, jitter, admission |
| Operations | connected count | convergence time, census, wave vs control |

## 1 · Requirements

Clarifying: offline daily, some for weeks · a bricked device costs ~$150 · 5 hardware revs, 3 carriers, every region · devices are
untrusted · config, firmware, state, health in scope. FR1 Know · FR2 Configure · FR3 Release · FR4 Stop. NFR: ≤ 100 devices harmed per
release; 95 % of online devices on a config in 24 h; a release in ~2 weeks; 99.9 % control plane, devices run without it. IN /
OUT stated (the data plane is SD-97).

## 2 · Estimates

| Number | Arithmetic | Decides |
|---|---|---|
| Health reports | 1 M ÷ 300 s ≈ 3,300/s × 1 KB ≈ 3.3 MB/s | small: Kafka + TSDB |
| Connections | 1 M ÷ 100,000 = 10 nodes, ×2 | 20 MQTT nodes |
| Shadow | 1 M × 4 KB ≈ 4 GB | one PostgreSQL |
| Storm | 200,000 / 60 s ≈ 3,300/s; unjittered 40,000/s | jitter, admission |
| A release | 50 MB × 1 M = 50 TB; deltas ≈ 8 TB | a CDN |
| Bricking 1 % | 10,000 × $150 = $1.5 M | waves; budget 100 devices |
| Version tail | 7 years × 12 = 84 versions | every protocol stays supported |
| Certificates | 1 M ÷ 730 days ≈ 1,400 renewals a day | automatic renewal, grace, re-enrolment |
| Release budget | 2 + 2 + 1 + 2 + 3 ≈ 10 of 14 days | halts are normal |

## 3 · Theory

Is / is not (a bus, telemetry, app deployment) · S1 never bricked · S2 only signed, only its own · S3 bounded harm · L1 converge · L2
finish · tension figure · M1 desired/reported reconciled · edge vs level table · M2 identity + signed images · M3 waves by cohort with
auto-halt · M4 A/B + watchdog (`seq-th-ab`) · M5 jitter + admission · options: A push commands, B poll a URL, C shadow pushed to all,
D waves by percentage, **E shadow + cohort waves with auto-halt + A/B and watchdog** · failure catalogue.

## 4 · API and entities

Desired document (MQTT retained; version, image hash and signature, `min_firmware_for_config`) · reported document (applied,
rejected, blocked_on, seq, epoch) · `PUT /v1/cohorts/{c}/desired` with If-Match · `POST /v1/releases`. Entities: DEVICE, COHORT,
DESIRED DOC, REPORTED DOC (weak, versioned), RELEASE, IMAGE. Physical: `device`, `desired_doc`, `release`, `wave`, `reported_doc`,
TSDB by cohort.

## 5 · Design

| Version | Adds | Answers | Leaves |
|---|---|---|---|
| V1 | agent, gateway, shadow, fleet API | state with versions | offline devices; no health |
| V2 | reconciler, telemetry, metrics | convergence and health | releases go to everyone |
| V3 | rollout controller, image CDN | waves, signed images | is the fleet really converging? |
| V4 (ch. 6) | fleet census | convergence measured | — |

Flows: `flow-config`, `flow-release`. Sequences: `seq-report`, `seq-config`, `seq-release`, `seq-halt`; the cost of a halt.

## 5.1 · Components and technologies

Component views: device agent, rollout controller, device gateway.

<!-- stack:outline -->

| Container | Choice | How it is built | Rejected | Theory part |
|---|---|---|---|---|
| Device gateway | EMQX cluster, MQTT 5, mTLS | About 100,000 connections per node, 20 nodes | HTTP polling; Kafka on devices | 11 §11.6–11.7, 16 §16.1 |
| Shadow store | PostgreSQL, one row per device | One row per device: desired and reported JSON with versions | Redis; A replayed change log | 15 §15.2, 8 §8.2 |
| Firmware images | Object storage + CDN; images signed offline | The desired document names the URL, size, SHA-256 and an offline signature | Images through the brokers; Trusting TLS to the CDN | 7 §7.12, 16 §16.4 |
| Telemetry | Kafka → VictoriaMetrics, cohort labels | Summaries every 5 minutes with a per-device sequence; repeats dropped; metrics labelled by cohort, firmware and wave. | Device ID as a label; Scraping devices | 14 §14.3, 10 §10.5 |

Fix-slide rejections: 1: A server-side rollback command; 2: Rolling out to a percentage; 3: Replaying every queued change in order; 4: Immediate reconnect with a fixed retry; 5: Exactly-once delivery from the broker; 6: Dashboards of connected devices.

<!-- /stack:outline -->

## 5.2 · Alternate path

A managed device service, hourly polling, three manual release steps; keep A/B and the watchdog. Line: 1 % of 5,000 devices = $7,500;
of 1 M = $1.5 M; below ≈ 10,000 devices, ship it.

## 7 · Challenges

1. **A config that crashes the device (crux):** pending until confirmed; a try counter; the agent confirms only after a full round
   trip; three failures → last known good (`seq-ch1-brick`); what "healthy" means; push: a deaf agent → round-trip confirmation and a
   signed recovery path in the bootloader. Rejected: a server-side rollback command.
2. **The rare revision:** strata (every hw rev × region × carrier, ≥ 50 online devices each), per-cell controls, interval halts;
   waves figure; what a 1,000-device wave can see; push: noisy halts → intervals, halt-then-resume. Rejected: percentages.
3. **Six weeks offline:** latest desired document, prerequisites first, idempotent apply; level-triggered loop pseudocode; push:
   a wrong clock → versions order everything. Rejected: replaying queued changes.
4. **The reconnect storm:** full jitter, a token bucket per node with retry-after, version-compare cache; numbers; pseudocode; push:
   the shadow DB → current devices never read it. Rejected: fixed immediate retries.
5. **Telemetry, twice:** (epoch, seq) per device from flash; dedup; cohort labels, per-device data to the lake; pseudocode; push:
   small-wave statistics. Rejected: broker exactly-once.
6. **Connected is not converged (observability):** **V4** fleet census; convergence time; blocked and rejected; unseen; symptom
   pairs; SLIs. Rejected: connected-device dashboards.

## 8 · Recap

V4 with badges; one sentence per path; mistakes; thesis.

## Canon check

| Point | Covered at |
|---|---|
| Per-device identity, provisioning, rotation, revocation | M2, estimates "identity" |
| Desired vs reported state, reconciliation | M1, edge vs level, challenge 3 |
| Cohorts, staged rollout, halt and rollback | M3, challenge 2, the cost of a halt |
| A/B partitions and a watchdog | M4, challenge 1 |
| Store-and-forward telemetry with dedup; cardinality | challenge 5 |
| Connection storms | M5, challenge 4 |
| The long version tail | estimates; census |
| A kill switch on a device running bad software | challenge 1 push |
| Device application data | dismissed: SD-97's data plane |

## Budget (measured)

0: 336 · 1: 477 · 2: 289 · 3: 824 · 4: 287 · 5 (+5.1, 5.2): 1,366 · 6: 80 · 7: 2,889 · 8: 216 · **total 6,764 words (≈ 60 min)**.
